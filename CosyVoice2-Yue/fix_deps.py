#!/usr/bin/env python3
"""
Fix dependencies for CosyVoice2-Yue OpenAI Server
"""

import subprocess
import sys
import os

print("="*60)
print("Fixing Dependencies")
print("="*60)
print(f"Python: {sys.executable}")
print()

# Check if in venv
if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    print("⚠️  Not running in a virtual environment!")
    print("It's recommended to use a virtual environment:")
    print("  python3 -m venv .venv")
    print("  source .venv/bin/activate")
    print()
    response = input("Continue anyway? (y/n): ")
    if response.lower() != 'y':
        sys.exit(0)

packages = [
    "setuptools<70",         # Fix pkg_resources issue (setuptools 70+ removed it)
    "ruamel.yaml==0.18.6",   # Fix max_depth issue
    "HyperPyYAML",
    "lightning",
    "hydra-core",
    "omegaconf",
    "conformer",
    "wetext",                # TTS frontend (fallback for ttsfrd)
]

print("Installing/upgrading packages:")
for pkg in packages:
    print(f"  - {pkg}")

print()
print("Running pip install...")
print()

try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + packages)
    print()
    print("="*60)
    print("✓ Dependencies installed successfully!")
    print("="*60)
    print()
    print("Test the installation:")
    print("  python diagnose_imports.py")
    print()
    print("Then start the server:")
    print("  python openai_server.py --port 8201")
    print()
    print("Or use the launcher:")
    print("  ./launch_server.sh")
except subprocess.CalledProcessError as e:
    print()
    print("="*60)
    print(f"✗ Installation failed: {e}")
    print("="*60)
    sys.exit(1)
