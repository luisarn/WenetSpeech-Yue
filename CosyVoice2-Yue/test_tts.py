#!/usr/bin/env python3
"""
Testing program for CosyVoice2-Yue TTS models.
Tests both the base model and the ZoengJyutGaai (ZJG) variant.
"""

import sys
import os
import argparse

# Add third_party Matcha-TTS to path
sys.path.append('third_party/Matcha-TTS')

# Check for required dependencies before importing
try:
    import hyperpyyaml
except ImportError as e:
    print("Error: 'hyperpyyaml' is not installed.")
    print(f"\nCurrent Python: {sys.executable}")
    print(f"Python version: {sys.version}\n")
    print("To fix this, run one of the following:")
    print("  1. Install in current environment: pip install HyperPyYAML")
    print("  2. Install all dependencies: pip install -r requirements.txt")
    print("  3. Use 'python' instead of 'python3.10' if in a conda environment")
    sys.exit(1)

from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio

# Optional: OpenCC for Simplified to Traditional Chinese conversion
try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False
    print("Warning: opencc not installed. Simplified Chinese text will not be converted.")


def check_model_files(model_dir):
    """Check if all required model files exist."""
    required_files = [
        'cosyvoice2.yaml',
        'campplus.onnx',
        'speech_tokenizer_v2.onnx',
        'spk2info.pt',
        'llm.pt',
        'flow.pt',
        'hift.pt'
    ]
    missing = []
    for f in required_files:
        path = os.path.join(model_dir, f)
        if not os.path.exists(path):
            missing.append(f)
    return missing


def load_model(model_path, load_jit=False, load_trt=False, load_vllm=False, fp16=False):
    """Load a CosyVoice2 model from the given path."""
    import warnings
    warnings.filterwarnings('ignore')
    
    print(f"Loading model from: {model_path}")
    
    # Check if it's a local path or HF model ID
    if os.path.exists(model_path):
        # Local path
        missing = check_model_files(model_path)
        if missing:
            raise FileNotFoundError(f"Model directory missing files: {missing}")
    else:
        # HF model ID - will download
        print(f"Model not found locally. Will attempt to download from HuggingFace: {model_path}")
        print("Note: This may take a while for large models (several GB)...")
    
    model = CosyVoice2(
        model_path,
        load_jit=load_jit,
        load_trt=load_trt,
        load_vllm=load_vllm,
        fp16=fp16
    )
    print(f"Model loaded successfully. Sample rate: {model.sample_rate}")
    return model


def synthesize(model, text, instruct_text, prompt_speech, output_prefix, stream=False):
    """Synthesize speech using the given model and save to files."""
    print(f"\nSynthesizing with model '{output_prefix}':")
    print(f"  Text: {text[:50]}..." if len(text) > 50 else f"  Text: {text}")
    print(f"  Instruct: {instruct_text}")
    
    results = []
    for i, output in enumerate(model.inference_instruct2(text, instruct_text, prompt_speech, stream=stream)):
        output_file = f'{output_prefix}_{i}.wav'
        torchaudio.save(output_file, output['tts_speech'], model.sample_rate)
        print(f"  Saved: {output_file}")
        results.append(output_file)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Test CosyVoice2-Yue TTS models')
    parser.add_argument('--base-model', type=str, 
                        default='pretrained_models/Cosyvoice2-Yue',
                        help='Path to base CosyVoice2-Yue model (local path or HF model ID)')
    parser.add_argument('--zjg-model', type=str,
                        default='pretrained_models/Cosyvoice2-Yue-ZoengJyutGaai',
                        help='Path to ZoengJyutGaai (ZJG) variant model (local path or HF model ID)')
    parser.add_argument('--prompt-audio', type=str,
                        default='asset/sg_017_090.wav',
                        help='Path to prompt audio file (16kHz WAV)')
    parser.add_argument('--text', type=str,
                        default='收到朋友从远方寄嚟嘅生日礼物，嗰份意外嘅惊喜同埋深深嘅祝福令我心入面充满咗甜蜜嘅快乐，笑容好似花咁绽放。',
                        help='Text to synthesize')
    parser.add_argument('--instruct', type=str,
                        default='用粤语说这句话',
                        help='Instruction text for the model')
    parser.add_argument('--convert-s2t', action='store_true',
                        help='Convert Simplified Chinese to Traditional Chinese using OpenCC')
    parser.add_argument('--fp16', action='store_true',
                        help='Use FP16 mode (requires CUDA)')
    parser.add_argument('--load-jit', action='store_true',
                        help='Load JIT compiled models')
    parser.add_argument('--load-trt', action='store_true',
                        help='Load TensorRT models')
    parser.add_argument('--load-vllm', action='store_true',
                        help='Load VLLM models')
    parser.add_argument('--stream', action='store_true',
                        help='Use streaming inference')
    parser.add_argument('--test-base', action='store_true',
                        help='Test base model')
    parser.add_argument('--test-zjg', action='store_true',
                        help='Test ZJG model')
    parser.add_argument('--output-dir', type=str,
                        default='.',
                        help='Output directory for generated audio files')
    
    args = parser.parse_args()
    
    # Default to testing both models if none specified
    if not args.test_base and not args.test_zjg:
        args.test_base = True
        args.test_zjg = True
    
    # Create output directory if needed
    if args.output_dir != '.' and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Convert text if requested
    text = args.text
    if args.convert_s2t:
        if OPENCC_AVAILABLE:
            converter = opencc.OpenCC('s2t.json')
            text = converter.convert(text)
            print(f"Converted text: {text}")
        else:
            print("Warning: Cannot convert text - opencc not installed")
    
    # Load prompt audio
    print(f"\nLoading prompt audio: {args.prompt_audio}")
    if not os.path.exists(args.prompt_audio):
        print(f"Error: Prompt audio not found: {args.prompt_audio}")
        sys.exit(1)
    prompt_speech_16k = load_wav(args.prompt_audio, 16000)
    print(f"Prompt audio loaded: {prompt_speech_16k.shape}")
    
    # Test base model
    if args.test_base:
        try:
            cosyvoice_base = load_model(
                args.base_model,
                load_jit=args.load_jit,
                load_trt=args.load_trt,
                load_vllm=args.load_vllm,
                fp16=args.fp16
            )
            output_prefix = os.path.join(args.output_dir, 'base')
            synthesize(cosyvoice_base, text, args.instruct, prompt_speech_16k, output_prefix, args.stream)
            del cosyvoice_base
        except FileNotFoundError as e:
            print(f"\nSkipping base model: {e}")
        except Exception as e:
            print(f"\nError with base model: {e}")
            import traceback
            traceback.print_exc()
    
    # Test ZJG model
    if args.test_zjg:
        try:
            cosyvoice_zjg = load_model(
                args.zjg_model,
                load_jit=args.load_jit,
                load_trt=args.load_trt,
                load_vllm=args.load_vllm,
                fp16=args.fp16
            )
            output_prefix = os.path.join(args.output_dir, 'zjg')
            synthesize(cosyvoice_zjg, text, args.instruct, prompt_speech_16k, output_prefix, args.stream)
            del cosyvoice_zjg
        except FileNotFoundError as e:
            print(f"\nSkipping ZJG model: {e}")
        except Exception as e:
            print(f"\nError with ZJG model: {e}")
            import traceback
            traceback.print_exc()
    
    print("\nTesting completed!")


if __name__ == '__main__':
    main()
