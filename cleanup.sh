#!/bin/bash
# Safe cleanup script for WenetSpeech-Yue project
# Run this from the project root

set -e

echo "================================"
echo "WenetSpeech-Yue Project Cleanup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Count files before cleanup
echo "Counting files before cleanup..."
CACHE_COUNT=$(find . -type f \( -name "*.pyc" -o -name "*.pyo" \) ! -path "./.venv/*" ! -path "./CosyVoice2-Yue/.venv/*" 2>/dev/null | wc -l)
DS_COUNT=$(find . -name ".DS_Store" -type f 2>/dev/null | wc -l)

echo "  Python cache files: $CACHE_COUNT"
echo "  .DS_Store files: $DS_COUNT"
echo ""

# 1. Python cache files
echo -e "${YELLOW}1. Removing Python cache files...${NC}"
find . -type d -name "__pycache__" ! -path "./.venv/*" ! -path "./CosyVoice2-Yue/.venv/*" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" ! -path "./.venv/*" ! -path "./CosyVoice2-Yue/.venv/*" -delete 2>/dev/null || true
find . -type f -name "*.pyo" ! -path "./.venv/*" ! -path "./CosyVoice2-Yue/.venv/*" -delete 2>/dev/null || true
echo -e "${GREEN}   ✓ Done${NC}"

# 2. macOS .DS_Store files
echo -e "${YELLOW}2. Removing .DS_Store files...${NC}"
find . -name ".DS_Store" -type f -delete 2>/dev/null || true
echo -e "${GREEN}   ✓ Done${NC}"

# 3. Test output files (optional)
echo -e "${YELLOW}3. Checking test output directories...${NC}"
if [ -d "CosyVoice2-Yue/output" ] || [ -d "CosyVoice2-Yue/output_female" ]; then
    echo "   Found test output directories:"
    [ -d "CosyVoice2-Yue/output" ] && echo "     - CosyVoice2-Yue/output/"
    [ -d "CosyVoice2-Yue/output_female" ] && echo "     - CosyVoice2-Yue/output_female/"
    read -p "   Remove these directories? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf CosyVoice2-Yue/output/ CosyVoice2-Yue/output_female/ 2>/dev/null || true
        echo -e "${GREEN}   ✓ Removed${NC}"
    else
        echo "   Skipped"
    fi
else
    echo "   None found"
fi

# 4. .python-version file
echo -e "${YELLOW}4. Checking .python-version file...${NC}"
if [ -f "CosyVoice2-Yue/.python-version" ]; then
    read -p "   Remove CosyVoice2-Yue/.python-version? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f CosyVoice2-Yue/.python-version
        echo -e "${GREEN}   ✓ Removed${NC}"
    else
        echo "   Kept"
    fi
else
    echo "   None found"
fi

# 5. Check for potential duplicate voice files
echo ""
echo -e "${YELLOW}5. Checking for potential duplicate voice files...${NC}"
if [ -f "CosyVoice2-Yue/asset/hk_female_2.wav" ]; then
    echo "   ⚠️  Found: CosyVoice2-Yue/asset/hk_female_2.wav (13MB)"
    echo "      This appears to be a duplicate of hk_female.wav"
    read -p "   Remove this file? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f CosyVoice2-Yue/asset/hk_female_2.wav
        echo -e "${GREEN}   ✓ Removed${NC}"
    else
        echo "   Kept"
    fi
fi

if [ -f "CosyVoice2-Yue/asset/luis_neng.wav" ]; then
    echo "   ⚠️  Found: CosyVoice2-Yue/asset/luis_neng.wav (1.4MB)"
    echo "      This appears to be a personal voice file"
    read -p "   Remove this file? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f CosyVoice2-Yue/asset/luis_neng.wav
        echo -e "${GREEN}   ✓ Removed${NC}"
    else
        echo "   Kept"
    fi
fi

echo ""
echo "================================"
echo -e "${GREEN}Cleanup complete!${NC}"
echo "================================"
echo ""
echo "To see what else can be cleaned up, check:"
echo "  cat CLEANUP_REPORT.md"
