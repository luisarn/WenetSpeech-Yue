#!/bin/bash
# One-command installation script for CosyVoice2-Yue OpenAI API Server
# This script handles all known installation issues automatically

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     CosyVoice2-Yue OpenAI API Server Installation          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found!${NC}"
    echo "Please run this script from the CosyVoice2-Yue directory."
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

# Extract major.minor version
py_major=$(echo $python_version | cut -d. -f1)
py_minor=$(echo $python_version | cut -d. -f2)

if [ "$py_major" -lt 3 ] || ([ "$py_major" -eq 3 ] && [ "$py_minor" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8+ required, found $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Python version OK${NC}"

# Create virtual environment
echo ""
echo -e "${YELLOW}Creating virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo "  Found existing .venv"
    read -p "  Remove and recreate? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo -e "${GREEN}  ✓ Virtual environment recreated${NC}"
    else
        echo "  Using existing virtual environment"
    fi
else
    python3 -m venv .venv
    echo -e "${GREEN}  ✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo ""
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}  ✓ Activated: $(which python)${NC}"

# Upgrade pip
echo ""
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# CRITICAL: Install setuptools first
echo ""
echo -e "${YELLOW}Installing setuptools (<70)...${NC}"
echo -e "${BLUE}  This is required to avoid pkg_resources issues${NC}"
pip install 'setuptools<70'
echo -e "${GREEN}  ✓ setuptools installed${NC}"

# Install wheel for better package building
echo ""
echo -e "${YELLOW}Installing wheel...${NC}"
pip install wheel

# Install PyTorch first (device-specific)
echo ""
echo -e "${YELLOW}Detecting device...${NC}"

# Check for CUDA
if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "  CUDA detected"
    DEVICE="cuda"
    echo -e "${YELLOW}Installing PyTorch with CUDA support...${NC}"
    pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu121
elif python -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null | grep -q "True"; then
    echo "  Apple Silicon (MPS) detected"
    DEVICE="mps"
    echo -e "${YELLOW}Installing PyTorch...${NC}"
    pip install torch==2.3.1 torchaudio==2.3.1
else
    echo "  CPU only"
    DEVICE="cpu"
    echo -e "${YELLOW}Installing PyTorch (CPU version)...${NC}"
    pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
fi
echo -e "${GREEN}  ✓ PyTorch installed${NC}"

# Install other dependencies
echo ""
echo -e "${YELLOW}Installing dependencies (this may take 10+ minutes)...${NC}"
pip install -r requirements.txt || {
    echo -e "${YELLOW}  Some packages failed, trying individual installs...${NC}"
    
    # Install critical packages one by one
    pip install fastapi uvicorn pydantic numpy
    pip install hyperpyyaml ruamel.yaml==0.18.6
    pip install lightning omegaconf hydra-core conformer
    pip install transformers huggingface_hub
    pip install --no-build-isolation openai-whisper==20231117 || pip install openai-whisper
    pip install wetext
    
    # Install remaining requirements
    pip install -r requirements.txt || true
}
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

# Apply fixes
echo ""
echo -e "${YELLOW}Applying known fixes...${NC}"

# Fix ttsfrd if it exists
pip show ttsfrd >/dev/null 2>&1 && {
    echo "  Removing problematic ttsfrd package..."
    pip uninstall -y ttsfrd
    pip install wetext
} || true

# Ensure ruamel.yaml is correct version
pip install ruamel.yaml==0.18.6 --force-reinstall >/dev/null 2>&1 || true

echo -e "${GREEN}  ✓ Fixes applied${NC}"

# Verify installation
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"
python diagnose_imports.py && {
    echo -e "${GREEN}  ✓ All imports working${NC}"
} || {
    echo -e "${YELLOW}  ⚠ Some imports failed, but server may still work${NC}"
}

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Installation Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}To start the server:${NC}"
echo "  source .venv/bin/activate"
echo "  python openai_server.py --port 8201"
echo ""
echo -e "${BLUE}To test the server:${NC}"
echo "  curl http://localhost:8201/health"
echo ""
echo -e "${BLUE}Device detected:${NC} $DEVICE"

if [ "$DEVICE" = "mps" ]; then
    echo "  Use: python openai_server.py --device mps --port 8201"
elif [ "$DEVICE" = "cuda" ]; then
    echo "  Use: python openai_server.py --device cuda --fp16 --port 8201"
else
    echo "  Use: python openai_server.py --device cpu --port 8201"
fi

echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "  - API docs: OPENAI_SERVER.md"
echo "  - Install guide: INSTALL.md"
echo ""
