#!/usr/bin/env python3
"""
Diagnose import issues with CosyVoice2
"""

import sys
import os

print("="*60)
print("Diagnosing Import Issues")
print("="*60)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Virtual env: {os.environ.get('VIRTUAL_ENV', 'Not activated')}")
print()

# Check if we're in a venv
in_venv = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
)
print(f"Running in virtual environment: {in_venv}")
print()

# Check each problematic import
imports_to_check = [
    ('hyperpyyaml', 'HyperPyYAML'),
    ('lightning', 'lightning'),
    ('hydra', 'hydra-core'),
    ('omegaconf', 'omegaconf'),
    ('conformer', 'conformer'),
    ('ruamel.yaml', 'ruamel.yaml'),
    ('torch', 'torch'),
    ('torchaudio', 'torchaudio'),
]

print("Checking imports:")
all_ok = True
for module_name, pip_name in imports_to_check:
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        location = getattr(module, '__file__', 'unknown')
        print(f"  ✓ {module_name:20} ({pip_name})")
        print(f"      Version: {version}")
        print(f"      Location: {location[:60]}...")
    except ImportError as e:
        print(f"  ✗ {module_name:20} ({pip_name}) - NOT FOUND")
        print(f"      Error: {e}")
        all_ok = False

print()

# Try importing cosyvoice
print("Checking CosyVoice2 import:")
sys.path.insert(0, '.')
sys.path.insert(0, 'third_party/Matcha-TTS')

try:
    from cosyvoice.cli.cosyvoice import CosyVoice2
    print("  ✓ CosyVoice2 can be imported")
except Exception as e:
    print(f"  ✗ CosyVoice2 import failed: {e}")
    import traceback
    print()
    print("Full traceback:")
    traceback.print_exc()
    all_ok = False

print()
print("="*60)
if all_ok:
    print("✓ All imports working!")
    print()
    print("You can start the server with:")
    print("  python openai_server.py --port 8201")
else:
    print("✗ Some imports failed")
    print()
    print("If you're using a virtual environment, make sure it's activated:")
    print("  source .venv/bin/activate")
    print()
    print("Then install missing packages:")
    print("  pip install hyperpyyaml lightning hydra-core omegaconf conformer")
    print()
    print("Or use the launcher script:")
    print("  ./launch_server.sh")
print("="*60)
