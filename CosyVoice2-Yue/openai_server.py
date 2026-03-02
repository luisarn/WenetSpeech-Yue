#!/usr/bin/env python3
"""
OpenAI API Compatible Server for CosyVoice2-Yue
Implements the /v1/audio/speech endpoint for TTS
Supports CUDA, MPS (Apple Silicon), and CPU
"""

import os
import sys
import argparse
import logging
import io
import base64
import json
from typing import Optional
from pathlib import Path

logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add paths for cosyvoice
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'third_party/Matcha-TTS'))

# Check dependencies before importing
def check_dependencies():
    """Check if required dependencies are installed"""
    missing = []
    
    try:
        import fastapi
    except ImportError:
        missing.append('fastapi')
    
    try:
        import uvicorn
    except ImportError:
        missing.append('uvicorn')
    
    try:
        import pydantic
    except ImportError:
        missing.append('pydantic')
    
    try:
        import torch
    except ImportError:
        missing.append('torch')
    
    try:
        import torchaudio
    except ImportError:
        missing.append('torchaudio')
    
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    if missing:
        print("❌ Missing required dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        sys.exit(1)

check_dependencies()

# Fix for hyperpyyaml compatibility with ruamel.yaml
try:
    import ruamel.yaml
    if hasattr(ruamel.yaml, 'YAML'):
        from ruamel.yaml.main import YAML
        original_init = YAML.__init__
        
        def patched_init(self, *args, **kwargs):
            if 'max_depth' in kwargs and not hasattr(self, 'max_depth'):
                kwargs.pop('max_depth')
            original_init(self, *args, **kwargs)
        
        YAML.__init__ = patched_init
except Exception:
    pass

import torch
import torchaudio

# Global device setting (set before importing cosyvoice)
DEVICE = os.environ.get('COZYVOICE_DEVICE', 'auto')

def get_device(preferred_device='auto'):
    """Get the best available device"""
    if preferred_device == 'auto':
        if torch.cuda.is_available():
            return torch.device('cuda')
        elif torch.backends.mps.is_available():
            return torch.device('mps')
        else:
            return torch.device('cpu')
    else:
        return torch.device(preferred_device)

# Monkey-patch for MPS/CPU support in cosyvoice models
original_cosyvoice_init = None
original_model_init = None

def patch_cosyvoice_device(device):
    """Patch CosyVoice to use specified device"""
    try:
        from cosyvoice.cli import model as model_module
        from cosyvoice.cli import cosyvoice as cosyvoice_module
        
        original_model_init = model_module.CosyVoiceModel.__init__
        original_cosyvoice_init = cosyvoice_module.CosyVoice.__init__
        
        def patched_model_init(self, llm, flow, hift, fp16=False):
            # Use our device instead of auto-detecting
            self.device = device
            self.llm = llm
            self.flow = flow
            self.hift = hift
            self.fp16 = fp16
            
            # Disable fp16 for MPS and CPU
            if device.type != 'cuda' and fp16:
                logging.warning(f'{device.type} device does not support fp16, disabling it')
                self.fp16 = False
            
            if self.fp16 is True:
                self.llm.half()
                self.flow.half()
            
            self.token_min_hop_len = 2 * self.flow.input_frame_rate
            self.token_max_hop_len = 4 * self.flow.input_frame_rate
            self.token_overlap_len = 20
            self.mel_overlap_len = int(self.token_overlap_len / self.flow.input_frame_rate * 22050 / 256)
            self.mel_window = __import__('numpy').hamming(2 * self.mel_overlap_len)
            self.mel_cache_len = 20
            self.source_cache_len = int(self.mel_cache_len * 256)
            self.speech_window = __import__('numpy').hamming(2 * self.source_cache_len)
            self.stream_scale_factor = 1
            assert self.stream_scale_factor >= 1, 'stream_scale_factor should be greater than 1'
            
            # Context for MPS/CUDA
            if device.type == 'cuda':
                self.llm_context = torch.cuda.stream(torch.cuda.Stream(self.device))
            else:
                from contextlib import nullcontext
                self.llm_context = nullcontext()
            
            import threading
            self.lock = threading.Lock()
            self.tts_speech_token_dict = {}
            self.llm_end_dict = {}
            self.mel_overlap_dict = {}
            self.flow_cache_dict = {}
            self.hift_cache_dict = {}
        
        model_module.CosyVoiceModel.__init__ = patched_model_init
        
        # Also patch CosyVoice2 init to not override fp16 for non-CUDA devices
        original_cosyvoice2_init = cosyvoice_module.CosyVoice2.__init__
        
        def patched_cosyvoice2_init(self, model_dir, load_jit=False, load_trt=False, load_vllm=False, fp16=False, trt_concurrent=1):
            from hyperpyyaml import load_hyperpyyaml
            from huggingface_hub import snapshot_download
            from cosyvoice.cli.model import CosyVoice2Model
            from cosyvoice.utils.class_utils import get_model_type
            
            self.instruct = True if '-Instruct' in model_dir else False
            self.model_dir = model_dir
            self.fp16 = fp16
            
            if not os.path.exists(model_dir):
                model_dir = snapshot_download(model_dir)
            
            hyper_yaml_path = '{}/cosyvoice2.yaml'.format(model_dir)
            if not os.path.exists(hyper_yaml_path):
                raise ValueError('{} not found!'.format(hyper_yaml_path))
            
            with open(hyper_yaml_path, 'r') as f:
                configs = load_hyperpyyaml(f, overrides={'qwen_pretrain_path': os.path.join(model_dir, 'CosyVoice-BlankEN')})
            
            assert get_model_type(configs) == CosyVoice2Model, 'do not use {} for CosyVoice2 initialization!'.format(model_dir)
            
            from cosyvoice.cli.frontend import CosyVoiceFrontEnd
            self.frontend = CosyVoiceFrontEnd(configs['get_tokenizer'],
                                              configs['feat_extractor'],
                                              '{}/campplus.onnx'.format(model_dir),
                                              '{}/speech_tokenizer_v2.onnx'.format(model_dir),
                                              '{}/spk2info.pt'.format(model_dir),
                                              configs['allowed_special'])
            self.sample_rate = configs['sample_rate']
            
            # Disable fp16/jit/trt for non-CUDA devices
            if device.type != 'cuda' and (load_jit or load_trt or fp16):
                logging.warning(f'{device.type} device detected, disabling fp16/jit/trt')
                load_jit, load_trt, fp16 = False, False, False
            
            self.model = CosyVoice2Model(configs['llm'], configs['flow'], configs['hift'], fp16)
            self.model.load('{}/llm.pt'.format(model_dir),
                            '{}/flow.pt'.format(model_dir),
                            '{}/hift.pt'.format(model_dir))
            
            if load_vllm:
                self.model.load_vllm('{}/vllm'.format(model_dir))
            if load_jit:
                self.model.load_jit('{}/flow.encoder.{}.zip'.format(model_dir, 'fp16' if self.fp16 is True else 'fp32'))
            if load_trt:
                self.model.load_trt('{}/flow.decoder.estimator.{}.mygpu.plan'.format(model_dir, 'fp16' if self.fp16 is True else 'fp32'),
                                    '{}/flow.decoder.estimator.fp32.onnx'.format(model_dir),
                                    trt_concurrent,
                                    self.fp16)
            del configs
        
        cosyvoice_module.CosyVoice2.__init__ = patched_cosyvoice2_init
        
        logging.info(f"Patched CosyVoice to use device: {device}")
        
    except Exception as e:
        logging.warning(f"Could not patch CosyVoice device: {e}")

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

# Try to import CosyVoice2
try:
    from cosyvoice.cli.cosyvoice import CosyVoice2
    from cosyvoice.utils.file_utils import load_wav
except ImportError as e:
    error_msg = str(e)
    logging.error(f"Failed to import CosyVoice2: {e}")
    
    if "hyperpyyaml" in error_msg:
        logging.error("")
        logging.error("❌ hyperpyyaml is not installed. Install with:")
        logging.error("   pip install HyperPyYAML")
    elif "max_depth" in error_msg:
        logging.error("")
        logging.error("❌ Version incompatibility between hyperpyyaml and ruamel.yaml")
        logging.error("   Fix with: pip install ruamel.yaml==0.18.6")
    elif "conformer" in error_msg:
        logging.error("")
        logging.error("❌ conformer is not installed. Install with:")
        logging.error("   pip install conformer")
    else:
        logging.error("")
        logging.error("❌ Missing dependencies. Install with:")
        logging.error("   pip install -r requirements.txt")
    
    logging.error("")
    logging.error("Run diagnostic for more details:")
    logging.error("   python check_server.py")
    sys.exit(1)

# Create FastAPI app
app = FastAPI(
    title="CosyVoice2-Yue OpenAI API",
    description="OpenAI-compatible API server for CosyVoice2-Yue TTS",
    version="1.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
cosyvoice = None

# Default voice mappings
DEFAULT_VOICES = {
    # OpenAI-style voices
    "alloy": "asset/sg_017_090.wav",
    "echo": "asset/sg_017_090.wav",
    "fable": "asset/F01_中立_20054.wav",
    "onyx": "asset/sg_017_090.wav",
    "nova": "asset/F01_中立_20054.wav",
    "shimmer": "asset/F01_中立_20054.wav",
    # Cantonese voices
    "yue_male": "asset/yue_male.wav",
    "yue_female": "asset/yue_female.wav",
    "hk_male": "asset/hk_male.wav",
    "hk_female": "asset/hk_female.wav",
}

DEFAULT_INSTRUCT_TEXT = "用粤语说这句话"


class SpeechRequest(BaseModel):
    """OpenAI TTS API request model"""
    model: str = Field(default="cosyvoice2-yue", description="Model ID to use for synthesis")
    input: str = Field(..., description="Text to synthesize (max 4096 characters)", max_length=4096)
    voice: str = Field(default="hk_female", description="Voice to use for synthesis")
    response_format: Optional[str] = Field(
        default="mp3", description="Audio format: mp3, opus, aac, flac, wav, pcm"
    )
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0, description="Speech speed multiplier")
    instruct_text: Optional[str] = Field(
        default=None, 
        description="Instruction text for voice cloning (default: '用粤语说这句话')"
    )
    prompt_audio: Optional[str] = Field(
        default=None,
        description="Base64-encoded prompt audio data (overrides voice mapping)"
    )


class ModelInfo(BaseModel):
    """Model info for /v1/models endpoint"""
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    """Models list response"""
    object: str = "list"
    data: list


def get_voice_audio(voice: str, prompt_audio_b64: Optional[str] = None) -> tuple:
    """Get the prompt audio for a given voice."""
    if prompt_audio_b64:
        try:
            audio_bytes = base64.b64decode(prompt_audio_b64)
            return audio_bytes, True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {str(e)}")
    
    voice_lower = voice.lower()
    if voice_lower in DEFAULT_VOICES:
        audio_path = os.path.join(ROOT_DIR, DEFAULT_VOICES[voice_lower])
        if os.path.exists(audio_path):
            return audio_path, False
    
    if os.path.exists(voice):
        return voice, False
    
    default_path = os.path.join(ROOT_DIR, DEFAULT_VOICES["hk_female"])
    if os.path.exists(default_path):
        logging.warning(f"Voice '{voice}' not found, using default voice (hk_female)")
        return default_path, False
    
    raise HTTPException(status_code=400, detail=f"Voice '{voice}' not found and no default available")


def load_prompt_audio(audio_source, is_base64=False):
    """Load prompt audio from file path or base64 bytes"""
    if is_base64:
        temp_path = "/tmp/temp_prompt_audio.wav"
        with open(temp_path, "wb") as f:
            f.write(audio_source)
        return load_wav(temp_path, 16000)
    else:
        return load_wav(audio_source, 16000)


def generate_audio_data(model_output, output_format: str, sample_rate: int):
    """Generate audio data in the requested format."""
    audio_chunks = []
    for output in model_output:
        audio_chunks.append(output['tts_speech'])
    
    if not audio_chunks:
        raise HTTPException(status_code=500, detail="No audio generated")
    
    full_audio = torch.cat(audio_chunks, dim=1)
    buffer = io.BytesIO()
    
    if output_format == "pcm":
        audio_np = (full_audio.numpy() * (2 ** 15)).astype(np.int16)
        return audio_np.tobytes()
    
    elif output_format == "wav":
        torchaudio.save(buffer, full_audio, sample_rate, format="wav")
        return buffer.getvalue()
    
    elif output_format in ["mp3", "opus", "aac", "flac"]:
        if output_format == "flac":
            torchaudio.save(buffer, full_audio, sample_rate, format="flac")
            return buffer.getvalue()
        else:
            logging.warning(f"Format '{output_format}' not fully supported, returning WAV")
            torchaudio.save(buffer, full_audio, sample_rate, format="wav")
            buffer.seek(0)
            return buffer.getvalue()
    
    else:
        torchaudio.save(buffer, full_audio, sample_rate, format="wav")
        return buffer.getvalue()


def get_content_type(format: str) -> str:
    """Get MIME content type for audio format"""
    content_types = {
        "mp3": "audio/mpeg",
        "opus": "audio/opus",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "wav": "audio/wav",
        "pcm": "audio/pcm",
    }
    return content_types.get(format, "audio/wav")


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI compatible)"""
    return ModelsResponse(
        object="list",
        data=[
            ModelInfo(
                id="cosyvoice2-yue",
                object="model",
                created=1704067200,
                owned_by="wenetspeech-yue"
            ),
            ModelInfo(
                id="cosyvoice2-yue-zjg",
                object="model",
                created=1704067200,
                owned_by="wenetspeech-yue"
            )
        ]
    )


@app.post("/v1/audio/speech")
async def create_speech(request: SpeechRequest, authorization: Optional[str] = Header(None)):
    """Create speech from text (OpenAI TTS API compatible)."""
    global cosyvoice
    
    if cosyvoice is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        audio_source, is_base64 = get_voice_audio(request.voice, request.prompt_audio)
        prompt_speech_16k = load_prompt_audio(audio_source, is_base64)
        instruct_text = request.instruct_text or DEFAULT_INSTRUCT_TEXT
        
        logging.info(f"Synthesizing text: {request.input[:50]}... with voice: {request.voice}")
        
        model_output = cosyvoice.inference_instruct2(
            request.input,
            instruct_text,
            prompt_speech_16k,
            stream=False,
            speed=request.speed
        )
        
        audio_data = generate_audio_data(model_output, request.response_format, cosyvoice.sample_rate)
        
        content_type = get_content_type(request.response_format)
        return Response(
            content=audio_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename=speech.{request.response_format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during synthesis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global DEVICE
    
    device_info = {
        "type": DEVICE.type if hasattr(DEVICE, 'type') else str(DEVICE),
        "name": torch.cuda.get_device_name(0) if torch.cuda.is_available() and DEVICE.type == 'cuda' else 
                'Apple Silicon (MPS)' if DEVICE.type == 'mps' else 'CPU'
    }
    
    return {
        "status": "healthy",
        "model_loaded": cosyvoice is not None,
        "sample_rate": cosyvoice.sample_rate if cosyvoice else None,
        "device": device_info
    }


@app.get("/v1/voices")
async def list_voices():
    """List available voices and their mappings"""
    voices_info = {}
    for voice, path in DEFAULT_VOICES.items():
        full_path = os.path.join(ROOT_DIR, path)
        voices_info[voice] = {
            "path": path,
            "exists": os.path.exists(full_path)
        }
    return {
        "voices": voices_info,
        "default_instruct": DEFAULT_INSTRUCT_TEXT
    }


def load_model(model_path, args):
    """Load the CosyVoice2 model"""
    logging.info(f"Loading CosyVoice2 model from: {model_path}")
    
    if not os.path.exists(model_path):
        logging.info(f"Model not found locally, will download from HuggingFace: {model_path}")
        logging.info("This may take a while for large models (several GB)...")
    
    try:
        model = CosyVoice2(
            model_path,
            load_jit=args.load_jit,
            load_trt=args.load_trt,
            load_vllm=args.load_vllm,
            fp16=args.fp16
        )
        logging.info(f"Model loaded successfully! Sample rate: {model.sample_rate}")
        return model
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="OpenAI API Compatible Server for CosyVoice2-Yue (with MPS support)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8201,
        help="Port to run the server on"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to"
    )
    parser.add_argument(
        "--model_dir",
        type=str,
        default="pretrained_models/Cosyvoice2-Yue",
        help="Path to CosyVoice2-Yue model directory or HuggingFace model ID"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use for inference (auto selects best available)"
    )
    parser.add_argument(
        "--fp16",
        action="store_true",
        help="Use FP16 mode (only for CUDA)"
    )
    parser.add_argument(
        "--load_jit",
        action="store_true",
        help="Load JIT compiled models (only for CUDA)"
    )
    parser.add_argument(
        "--load_trt",
        action="store_true",
        help="Load TensorRT models (only for CUDA)"
    )
    parser.add_argument(
        "--load_vllm",
        action="store_true",
        help="Load VLLM models"
    )
    parser.add_argument(
        "--skip_model_check",
        action="store_true",
        help="Skip model loading check at startup"
    )
    
    args = parser.parse_args()
    
    global DEVICE
    DEVICE = get_device(args.device)
    
    logging.info(f"Using device: {DEVICE}")
    
    # Disable fp16/jit/trt for non-CUDA devices
    if DEVICE.type != 'cuda':
        if args.fp16:
            logging.warning(f"FP16 not supported on {DEVICE.type}, disabling")
            args.fp16 = False
        if args.load_jit:
            logging.warning(f"JIT not supported on {DEVICE.type}, disabling")
            args.load_jit = False
        if args.load_trt:
            logging.warning(f"TensorRT not supported on {DEVICE.type}, disabling")
            args.load_trt = False
    
    # Patch CosyVoice to use our device
    patch_cosyvoice_device(DEVICE)
    
    global cosyvoice
    
    if not args.skip_model_check:
        try:
            cosyvoice = load_model(args.model_dir, args)
        except Exception as e:
            error_msg = str(e)
            logging.error(f"\nFailed to start server: {e}")
            
            if "max_depth" in error_msg:
                logging.error("")
                logging.error("❌ Version incompatibility between hyperpyyaml and ruamel.yaml")
                logging.error("   Fix with: pip install ruamel.yaml==0.18.6")
            elif "pkg_resources" in error_msg:
                logging.error("")
                logging.error("❌ Missing pkg_resources")
                logging.error("   Fix with: pip install 'setuptools<70'")
            elif "ttsfrd" in error_msg:
                logging.error("")
                logging.error("❌ ttsfrd error")
                logging.error("   Fix with: pip uninstall -y ttsfrd && pip install wetext")
            else:
                logging.error("\nTroubleshooting:")
                logging.error("1. Check your internet connection if downloading from HuggingFace")
                logging.error("2. Check disk space (model is several GB)")
                logging.error("3. Run diagnostic: python diagnose_imports.py")
            sys.exit(1)
    else:
        logging.info("Skipping model loading (--skip_model_check)")
    
    # Start server
    logging.info(f"Starting OpenAI API server on {args.host}:{args.port}")
    logging.info(f"Device: {DEVICE} ({'Apple Silicon' if DEVICE.type == 'mps' else DEVICE.type})")
    logging.info(f"Endpoints:")
    logging.info(f"  - POST /v1/audio/speech  - TTS synthesis")
    logging.info(f"  - GET  /v1/models        - List models")
    logging.info(f"  - GET  /v1/voices        - List available voices")
    logging.info(f"  - GET  /health           - Health check")
    
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
