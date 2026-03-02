# Installation Guide for CosyVoice2-Yue OpenAI API Server

This guide covers installation on macOS, Linux, and Windows (WSL).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Device-Specific Setup](#device-specific-setup)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8 | 3.10 |
| RAM | 8 GB | 16 GB |
| Disk | 10 GB | 20 GB |
| GPU | Optional | Apple Silicon (MPS) or NVIDIA (CUDA) |

### macOS Prerequisites

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and dependencies
brew install python@3.10
brew install libomp  # Required for ONNX Runtime

# Install pynini (required by WeTextProcessing)
brew install pynini
```

### Linux Prerequisites

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev
sudo apt-get install -y libsndfile1 ffmpeg

# For pynini
sudo apt-get install -y libfst-dev
```

---

## Quick Start

For experienced users:

```bash
cd CosyVoice2-Yue

# Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Fix setuptools FIRST (critical!)
pip install 'setuptools<70'

# Install dependencies
pip install -r requirements.txt

# Start server
python openai_server.py --port 8201
```

---

## Detailed Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/ASLP-lab/WenetSpeech-Yue.git
cd WenetSpeech-Yue/CosyVoice2-Yue
```

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

**Windows (WSL):**
```bash
python3.10 -m venv .venv
source .venv/bin/activate
```

**Windows (CMD/PowerShell):**
```cmd
python3.10 -m venv .venv
.venv\Scripts\activate
```

Verify activation:
```bash
which python  # Should show .venv/bin/python
python --version  # Should show 3.10.x
```

### Step 3: Fix setuptools (CRITICAL!)

**Must be done BEFORE installing other packages:**

```bash
pip install 'setuptools<70'
```

> ⚠️ **Why?** setuptools 70+ removed `pkg_resources` which is needed by several packages including `openai-whisper`.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This may take 5-10 minutes depending on your internet connection.

**If you get errors, try:**

```bash
# Install with specific index for PyTorch
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu

# Then install rest
pip install -r requirements.txt
```

### Step 5: Fix Common Dependency Issues

Run the fix script to handle known issues:

```bash
python fix_deps.py
```

Or manually fix if needed:

```bash
# Fix hyperpyyaml/ruamel.yaml incompatibility
pip install ruamel.yaml==0.18.6

# Fix ttsfrd issue (if present)
pip uninstall -y ttsfrd
pip install wetext
```

### Step 6: Verify Installation

```bash
# Run diagnostics
python diagnose_imports.py

# Expected output: All imports should show ✓
```

---

## Device-Specific Setup

### Apple Silicon (M1/M2/M3)

MPS (Metal Performance Shaders) is automatically detected.

```bash
# Verify MPS is available
python -c "import torch; print(f'MPS available: {torch.backends.mps.is_available()}')"

# Start server with MPS
python openai_server.py --device mps --port 8201
```

**Note:** First inference may be slower due to MPS graph compilation.

### NVIDIA GPU (CUDA)

Ensure CUDA is installed:

```bash
# Check CUDA version
nvidia-smi

# Install PyTorch with CUDA support
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# Start server with CUDA
python openai_server.py --device cuda --fp16 --port 8201
```

### CPU Only

```bash
# Start server with CPU
python openai_server.py --device cpu --port 8201
```

---

## Model Setup

### Option 1: Auto-download (Recommended)

The model will be automatically downloaded on first run:

```bash
python openai_server.py --port 8201
```

This downloads ~10GB from HuggingFace and may take 10-30 minutes depending on your connection.

### Option 2: Manual Download

```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('ASLP-lab/WSYue-TTS', local_dir='pretrained_models')"
```

### Option 3: Use HuggingFace Model ID

```bash
python openai_server.py --model_dir "ASLP-lab/Cosyvoice2-Yue" --port 8201
```

---

## Verification

### Test the Server

```bash
# Start server
python openai_server.py --port 8201

# In another terminal, test health endpoint
curl http://localhost:8201/health

# Test synthesis
curl -X POST http://localhost:8201/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input":"早晨，食咗早餐未呀？","voice":"hk_female"}' \
  --output test.wav
```

### Expected Health Response

```json
{
  "status": "healthy",
  "model_loaded": true,
  "sample_rate": 22050,
  "device": {
    "type": "mps",
    "name": "Apple Silicon (MPS)"
  }
}
```

---

## Troubleshooting

### Issue: `No module named 'pkg_resources'`

**Solution:**
```bash
pip install 'setuptools<70'
pip install -r requirements.txt
```

### Issue: `openai-whisper` build fails

**Solution:**
```bash
pip install 'setuptools<70' wheel
pip install --no-build-isolation openai-whisper==20231117
```

### Issue: `ModuleNotFoundError: No module named 'hyperpyyaml'`

**Solution:**
```bash
pip install HyperPyYAML
# Also fix ruamel.yaml version
pip install ruamel.yaml==0.18.6
```

### Issue: `ModuleNotFoundError: No module named 'conformer'`

**Solution:**
```bash
pip install conformer
```

### Issue: `module 'ttsfrd' has no attribute 'TtsFrontendEngine'`

**Solution:**
```bash
pip uninstall -y ttsfrd
pip install wetext
```

### Issue: `AssertionError: Torch not compiled with CUDA enabled`

**Solution:** Reinstall PyTorch with correct backend:

```bash
# For CPU
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu

# For CUDA 12.1
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121

# For MPS (macOS)
pip install torch==2.3.1 torchaudio==2.3.1
```

### Issue: Model download is slow/stuck

**Solution:** Use HuggingFace mirror (for China users):

```bash
export HF_ENDPOINT=https://hf-mirror.com
python openai_server.py --port 8201
```

Or download manually:
```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('ASLP-lab/WSYue-TTS', local_dir='pretrained_models', resume_download=True)"
```

### Issue: Port already in use

**Solution:** Use a different port:
```bash
python openai_server.py --port 8202
```

---

## One-Command Installation Script

Save as `install.sh` and run:

```bash
#!/bin/bash
set -e

echo "=== CosyVoice2-Yue Installation ==="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3.10 -m venv .venv
source .venv/bin/activate

# Fix setuptools
echo "Installing setuptools..."
pip install 'setuptools<70'

# Install dependencies
echo "Installing dependencies (this may take 10+ minutes)..."
pip install -r requirements.txt

# Fix known issues
echo "Applying fixes..."
python fix_deps.py 2>/dev/null || true

# Verify
echo "Verifying installation..."
python diagnose_imports.py

echo ""
echo "=== Installation Complete ==="
echo "Start the server with:"
echo "  source .venv/bin/activate"
echo "  python openai_server.py --port 8201"
```

Make executable and run:
```bash
chmod +x install.sh
./install.sh
```

---

## Docker Installation (Alternative)

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install 'setuptools<70' && \
    pip install -r requirements.txt

# Copy application
COPY . .

EXPOSE 8201

CMD ["python", "openai_server.py", "--port", "8201", "--host", "0.0.0.0"]
```

Build and run:
```bash
docker build -t cosyvoice2-yue .
docker run -p 8201:8201 cosyvoice2-yue
```

---

## Next Steps

After installation:

1. **Read the API documentation:** `OPENAI_SERVER.md`
2. **Test voice cloning:** See examples in `openai_client_example.py`
3. **Check available voices:** `curl http://localhost:8201/v1/voices`

---

## Getting Help

If you encounter issues not covered here:

1. Run diagnostics: `python diagnose_imports.py`
2. Check server status: `python check_server.py`
3. Review troubleshooting: See `OPENAI_SERVER.md` Troubleshooting section
4. Check GitHub Issues: https://github.com/ASLP-lab/WenetSpeech-Yue/issues
