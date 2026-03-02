#!/usr/bin/env python3
"""
Fix for hyperpyyaml compatibility issue with ruamel.yaml
Error: 'Loader' object has no attribute 'max_depth'
"""

import subprocess
import sys

print("Checking hyperpyyaml and ruamel.yaml versions...")

# Check current versions
try:
    import hyperpyyaml
    print(f"hyperpyyaml: {hyperpyyaml.__version__ if hasattr(hyperpyyaml, '__version__') else 'unknown'}")
except ImportError:
    print("hyperpyyaml: not installed")

try:
    import ruamel.yaml
    print(f"ruamel.yaml: {ruamel.yaml.__version__}")
except ImportError:
    print("ruamel.yaml: not installed")

print("\nApplying fix...")

# The fix: downgrade ruamel.yaml to a compatible version
# or upgrade hyperpyyaml
try:
    # Try to upgrade hyperpyyaml first
    print("Upgrading hyperpyyaml...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "HyperPyYAML"])
    
    # If that doesn't work, downgrade ruamel.yaml
    print("Installing compatible ruamel.yaml version...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ruamel.yaml==0.18.6"])
    
    print("\n✓ Fix applied successfully!")
    print("Try running the server again:")
    print("  python openai_server.py --port 8201")
    
except subprocess.CalledProcessError as e:
    print(f"\n❌ Failed to apply fix: {e}")
    print("\nManual fix:")
    print("  pip install --upgrade HyperPyYAML")
    print("  pip install ruamel.yaml==0.18.6")
