# CosyVoice2-Yue OpenAI API Server

An OpenAI-compatible API server for CosyVoice2-Yue TTS (Text-to-Speech) model.

## Features

- **OpenAI API Compatible**: Drop-in replacement for OpenAI's TTS API
- **Zero-shot Voice Cloning**: Clone voices using reference audio
- **Multiple Output Formats**: Supports mp3, wav, flac, opus, aac, pcm
- **Streaming Support**: Ready for streaming implementation
- **Voice Mapping**: Pre-configured voice names mapped to reference audio files
- **Custom Voice Cloning**: Use your own reference audio for voice cloning

## Quick Start

### 1. Start the Server

```bash
cd CosyVoice2-Yue

# Basic startup (auto-detects best device: CUDA > MPS > CPU)
python openai_server.py

# With specific model
python openai_server.py --model_dir pretrained_models/Cosyvoice2-Yue

# Apple Silicon (M1/M2/M3) - use MPS for GPU acceleration
python openai_server.py --device mps

# Force CPU
python openai_server.py --device cpu

# With optimizations (CUDA only)
python openai_server.py --fp16 --load_vllm
```

The server will start on port `8201` by default.

**Device Options:**
- `--device auto` (default) - Automatically selects best available: CUDA > MPS > CPU
- `--device mps` - Apple Silicon GPU (M1/M2/M3 Macs)
- `--device cuda` - NVIDIA GPU
- `--device cpu` - CPU only

### 2. Use the API

#### Using OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8201/v1",
    api_key="dummy-api-key"  # Not used but required
)

response = client.audio.speech.create(
    model="cosyvoice2-yue",
    voice="alloy",
    input="收到朋友从远方寄嚟嘅生日礼物，嗰份意外嘅惊喜同埋深深嘅祝福令我心入面充满咗甜蜜嘅快乐。"
)

response.stream_to_file("output.mp3")
```

#### Using cURL

```bash
curl -X POST http://localhost:8201/v1/audio/speech \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy-api-key" \
  -d '{
    "model": "cosyvoice2-yue",
    "input": "收到朋友从远方寄嚟嘅生日礼物",
    "voice": "alloy",
    "response_format": "mp3"
  }' \
  --output output.mp3
```

#### Using the Example Client

```bash
# Synthesize with default voice
python openai_client_example.py --text "你好，世界"

# Synthesize with specific voice
python openai_client_example.py --voice "nova" --output "nova_output.wav"

# Use custom reference audio for voice cloning
python openai_client_example.py --prompt-audio "asset/sg_017_090.wav" --output "cloned.wav"

# List available voices
python openai_client_example.py --action list-voices

# Check server health
python openai_client_example.py --action health
```

## API Endpoints

### POST /v1/audio/speech

Create speech from text (OpenAI TTS API compatible).

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | No | Model ID (default: "cosyvoice2-yue") |
| `input` | string | Yes | Text to synthesize (max 4096 chars) |
| `voice` | string | No | Voice name (default: "alloy") |
| `response_format` | string | No | Audio format: mp3, opus, aac, flac, wav, pcm (default: mp3) |
| `speed` | float | No | Speech speed: 0.25 to 4.0 (default: 1.0) |
| `instruct_text` | string | No | Instruction for voice cloning (default: "用粤语说这句话") |
| `prompt_audio` | string | No | Base64-encoded custom reference audio |

**Example Request:**

```json
{
  "model": "cosyvoice2-yue",
  "input": "收到朋友从远方寄嚟嘅生日礼物",
  "voice": "alloy",
  "response_format": "wav",
  "speed": 1.0
}
```

**Response:** Audio file in the requested format.

### GET /v1/models

List available models.

### GET /v1/voices

List available voices and their mappings.

### GET /health

Health check endpoint.

## Voice Mapping

The server maps OpenAI-style voice names to reference audio files:

| Voice | Reference Audio |
|-------|----------------|
| `alloy` | `asset/sg_017_090.wav` |
| `echo` | `asset/sg_017_090.wav` |
| `fable` | `asset/F01_中立_20054.wav` |
| `onyx` | `asset/sg_017_090.wav` |
| `nova` | `asset/F01_中立_20054.wav` |
| `shimmer` | `asset/F01_中立_20054.wav` |

You can also use a direct file path as the `voice` parameter:

```json
{
  "voice": "/path/to/your/reference.wav"
}
```

Or provide base64-encoded audio in the `prompt_audio` field for custom voice cloning.

## Server Options

```bash
python openai_server.py --help
```

| Option | Description |
|--------|-------------|
| `--port` | Server port (default: 8201) |
| `--host` | Server host (default: 0.0.0.0) |
| `--model_dir` | Model directory or HuggingFace ID |
| `--fp16` | Use FP16 mode (requires CUDA) |
| `--load_jit` | Load JIT compiled models |
| `--load_trt` | Load TensorRT models |
| `--load_vllm` | Load VLLM models |
| `--device` | Device: `auto`, `cpu`, `cuda`, `mps` (default: auto) |

## Custom Voice Cloning

### Method 1: Add Voice to Mapping

Edit the `DEFAULT_VOICES` dictionary in `openai_server.py`:

```python
DEFAULT_VOICES = {
    "my_voice": "path/to/reference.wav",
    # ... existing voices
}
```

### Method 2: Use Direct Path

```bash
curl -X POST http://localhost:8201/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "你好",
    "voice": "path/to/reference.wav"
  }' \
  --output output.mp3
```

### Method 3: Base64 Audio

```python
import base64

with open("reference.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode("utf-8")

response = requests.post(
    "http://localhost:8201/v1/audio/speech",
    json={
        "input": "你好",
        "voice": "custom",
        "prompt_audio": audio_b64
    }
)
```

## Requirements

- Python 3.8+
- PyTorch
- FastAPI
- CosyVoice2-Yue dependencies (see `requirements.txt`)

## Notes

- The default instruction text is "用粤语说这句话" (Say this sentence in Cantonese)
- You can customize the instruction by providing the `instruct_text` parameter
- The model requires 16kHz mono WAV files as reference audio
- For best results, use reference audio between 3-10 seconds

## Troubleshooting

### Run Diagnostics First

If you encounter any issues, run the diagnostic scripts:

```bash
cd CosyVoice2-Yue

# Quick dependency check
python diagnose_imports.py

# Full server check
python check_server.py
```

### Virtual Environment Issues

**Problem:** Dependencies installed but server says they're missing

**Cause:** Your virtual environment might not be activated

**Solution:**

```bash
# Make sure your virtual environment is activated
source .venv/bin/activate  # or: source venv/bin/activate

# Verify you're using the right Python
which python3  # Should show .venv/bin/python3

# Then install dependencies in the venv
pip install -r requirements.txt

# Or use the launcher script which auto-activates
./launch_server.sh
```

### Import Errors (lightning, hydra-core, hyperpyyaml)

**Problem:** `ModuleNotFoundError` even after installing packages

**Quick Fix:**

```bash
# Run the automatic fix script
python fix_deps.py

# Or manually fix
source .venv/bin/activate
pip install ruamel.yaml==0.18.6
pip install --upgrade HyperPyYAML lightning hydra-core omegaconf conformer
```

### Apple Silicon (MPS) Issues

**Problem:** Model loads but inference is slow on Apple Silicon

**Solution:**
```bash
# Make sure you're using MPS device
python openai_server.py --device mps

# Check MPS is available
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"
```

**Note:** MPS support has some limitations:
- FP16 is not supported on MPS (automatically disabled)
- First inference may be slower due to MPS graph compilation
- Some operations may fall back to CPU

### pkg_resources Not Found

**Problem:** `ModuleNotFoundError: No module named 'pkg_resources'`

**Cause:** setuptools 70+ removed pkg_resources

**Solution:**

```bash
source .venv/bin/activate
pip install 'setuptools<70'
```

### ttsfrd Error (TtsFrontendEngine)

**Problem:** `module 'ttsfrd' has no attribute 'TtsFrontendEngine'`

**Cause:** A dummy ttsfrd package was installed instead of the real one

**Solution:**

```bash
source .venv/bin/activate
pip uninstall -y ttsfrd
pip install wetext
```

The code will automatically fall back to `wetext` which provides the same functionality.

### Version Incompatibility (max_depth error)

**Problem:** `'Loader' object has no attribute 'max_depth'`

**Solution:**

```bash
# Fix ruamel.yaml version
pip install ruamel.yaml==0.18.6

# Or run the fix script
python fix_hyperpyyaml.py
```

This will check:
- Python version
- Required dependencies
- CosyVoice2 import
- Model path
- Reference audio files

### Import Errors / Missing Dependencies

If you see errors like `No module named 'hyperpyyaml'` or `No module named 'conformer'`:

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install missing packages individually
pip install HyperPyYAML conformer lightning omegaconf hydra-core transformers huggingface_hub
```

### Model Loading Errors

**Model not found:**

Make sure the model directory exists or provide a HuggingFace model ID:

```bash
# Option 1: Download model first
python -c "from huggingface_hub import snapshot_download; snapshot_download('ASLP-lab/WSYue-TTS', local_dir='pretrained_models')"

# Option 2: Use HuggingFace model ID directly
python openai_server.py --model_dir "ASLP-lab/Cosyvoice2-Yue"
```

**Download stuck or slow:**

The model is several GB. If download is slow:
- Use a mirror: `export HF_ENDPOINT=https://hf-mirror.com` (for China users)
- Download manually from HuggingFace and place in `pretrained_models/`

### CUDA / GPU Errors

**CUDA out of memory:**

```bash
# Don't use FP16 or CUDA optimizations
python openai_server.py --fp16 False
```

**No CUDA device:**

The server works on CPU, but will be slower. No special flags needed - it automatically detects CUDA availability.

### Server Won't Start

**Port already in use:**

```bash
# Use a different port
python openai_server.py --port 8202
```

**Permission denied:**

```bash
# Use a port > 1024 (no root needed)
python openai_server.py --port 8201
```

### API Returns Errors

**503 Model not loaded:**

The model failed to load at startup. Check the server logs for the original error.

**400 Bad Request:**

- Check that `voice` is a valid voice name or file path
- Check that `input` text is not empty
- For custom voice, ensure base64 audio is valid

**500 Synthesis failed:**

- Check that reference audio files exist in `asset/`
- Ensure reference audio is 16kHz mono WAV format
- Check server logs for detailed error message

### Audio Quality Issues

- Ensure reference audio is 16kHz mono WAV
- Use reference audio with clear speech and minimal background noise (3-10 seconds)
- Adjust the `speed` parameter if speech is too fast/slow
- Try different voices to find the best match for your use case
