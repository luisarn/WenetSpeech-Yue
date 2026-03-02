#!/bin/bash
# Launcher script for CosyVoice2-Yue OpenAI API Server
# This ensures the virtual environment is used correctly

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo -e "${GREEN}Found virtual environment: .venv${NC}"
    
    # Check if already activated
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment..."
        source .venv/bin/activate
    else
        echo "Virtual environment already activated: $VIRTUAL_ENV"
    fi
elif [ -d "venv" ]; then
    echo -e "${GREEN}Found virtual environment: venv${NC}"
    
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Activating virtual environment..."
        source venv/bin/activate
    else
        echo "Virtual environment already activated: $VIRTUAL_ENV"
    fi
else
    echo -e "${YELLOW}Warning: No virtual environment found (.venv or venv)${NC}"
    echo "Using system Python: $(which python3)"
fi

echo ""
echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"
echo ""

# Check dependencies
echo "Checking dependencies..."
python3 -c "
import sys
missing = []
try:
    import hyperpyyaml
    print('  ✓ hyperpyyaml')
except ImportError:
    print('  ✗ hyperpyyaml - pip install HyperPyYAML')
    missing.append('HyperPyYAML')

try:
    import lightning
    print('  ✓ lightning')
except ImportError:
    print('  ✗ lightning - pip install lightning')
    missing.append('lightning')

try:
    import hydra
    print('  ✓ hydra')
except ImportError:
    print('  ✗ hydra - pip install hydra-core')
    missing.append('hydra-core')

try:
    import conformer
    print('  ✓ conformer')
except ImportError:
    print('  ✗ conformer - pip install conformer')
    missing.append('conformer')

try:
    import omegaconf
    print('  ✓ omegaconf')
except ImportError:
    print('  ✗ omegaconf - pip install omegaconf')
    missing.append('omegaconf')

if missing:
    print('')
    print('Missing dependencies. Install with:')
    print('  pip install ' + ' '.join(missing))
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}Please install missing dependencies and try again.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All dependencies found!${NC}"
echo ""

# Parse arguments
PORT=${1:-8201}
HOST=${2:-0.0.0.0}

echo "Starting CosyVoice2-Yue OpenAI API Server..."
echo "  Host: $HOST"
echo "  Port: $PORT"
echo ""

# Detect best device
python3 -c "import torch; print(f'Device: {torch.backends.mps.is_available()}')" 2>/dev/null | grep -q "True" && DEVICE="--device mps" || DEVICE=""

# Run the server
python3 openai_server.py --port "$PORT" --host "$HOST" $DEVICE
