#!/usr/bin/env python3
"""
Fix dependencies for CosyVoice2-Yue OpenAI Server
This script fixes all known dependency issues automatically.
"""

import subprocess
import sys
import os

print("="*60)
print("CosyVoice2-Yue Dependency Fixer")
print("="*60)
print(f"Python: {sys.executable}")
print()

# Check if in venv
if not (hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)):
    print("⚠️  Warning: Not running in a virtual environment!")
    print("It's recommended to use a virtual environment:")
    print("  python3 -m venv .venv")
    print("  source .venv/bin/activate")
    print()
    if input("Continue anyway? (y/n): ").lower() != 'y':
        sys.exit(0)

def run_command(cmd, description):
    """Run a pip command and handle errors"""
    print(f"  → {description}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip"] + cmd, 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.PIPE)
        print(f"     ✓ Done")
        return True
    except subprocess.CalledProcessError as e:
        print(f"     ✗ Failed (continuing anyway)")
        return False

print("Applying fixes...")
print()

# 1. Fix setuptools (CRITICAL - must be first)
print("1. Fixing setuptools...")
run_command(["install", "--upgrade", "'setuptools<70'"], 
            "Installing setuptools<70 (fixes pkg_resources)")

# 2. Install/upgrade wheel
print("\n2. Installing wheel...")
run_command(["install", "--upgrade", "wheel"], 
            "Installing wheel for better package building")

# 3. Fix ruamel.yaml version
print("\n3. Fixing ruamel.yaml...")
run_command(["install", "ruamel.yaml==0.18.6", "--force-reinstall"], 
            "Installing compatible ruamel.yaml version")

# 4. Install core dependencies that often fail
print("\n4. Installing core dependencies...")
packages = [
    ("HyperPyYAML", "HyperPyYAML"),
    ("lightning", "lightning"),
    ("hydra-core", "hydra-core"),
    ("omegaconf", "omegaconf"),
    ("conformer", "conformer"),
]

for module, pip_name in packages:
    try:
        __import__(module.replace('-', '_'))
        print(f"  ✓ {pip_name} already installed")
    except ImportError:
        run_command(["install", pip_name], f"Installing {pip_name}")

# 5. Fix ttsfrd issue
print("\n5. Checking ttsfrd...")
try:
    import ttsfrd
    print("  ⚠️  ttsfrd found (may cause issues)")
    if input("  Remove ttsfrd and install wetext instead? (y/n): ").lower() == 'y':
        run_command(["uninstall", "-y", "ttsfrd"], "Removing ttsfrd")
        run_command(["install", "wetext"], "Installing wetext")
except ImportError:
    print("  ✓ ttsfrd not installed (good)")
    try:
        import wetext
        print("  ✓ wetext already installed")
    except ImportError:
        run_command(["install", "wetext"], "Installing wetext")

# 6. Fix openai-whisper if needed
print("\n6. Checking openai-whisper...")
try:
    import whisper
    print("  ✓ openai-whisper already installed")
except ImportError:
    print("  Installing openai-whisper with --no-build-isolation...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--no-build-isolation", "openai-whisper==20231117"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print("     ✓ Done")
    except:
        run_command(["install", "openai-whisper"], 
                   "Installing openai-whisper (fallback)")

print()
print("="*60)
print("Fixes applied!")
print("="*60)
print()
print("Test the installation:")
print("  python diagnose_imports.py")
print()
print("Then start the server:")
print("  python openai_server.py --port 8201")
print()
