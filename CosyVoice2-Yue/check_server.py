#!/usr/bin/env python3
"""
Diagnostic script to check if the OpenAI API server can be started.
"""

import sys
import os

# Add paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, 'third_party/Matcha-TTS'))

def check_python_version():
    """Check Python version"""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print("✓ Python version OK")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\nChecking dependencies...")
    
    required = {
        'fastapi': ('FastAPI', 'fastapi'),
        'uvicorn': ('Uvicorn', 'uvicorn'),
        'pydantic': ('Pydantic', 'pydantic'),
        'torch': ('PyTorch', 'torch'),
        'torchaudio': ('TorchAudio', 'torchaudio'),
        'numpy': ('NumPy', 'numpy'),
        'hyperpyyaml': ('HyperPyYAML', 'hyperpyyaml'),
        'huggingface_hub': ('HuggingFace Hub', 'huggingface_hub'),
        'transformers': ('Transformers', 'transformers'),
        'lightning': ('Lightning', 'lightning'),
        'omegaconf': ('OmegaConf', 'omegaconf'),
        'hydra_core': ('Hydra', 'hydra-core'),
        'conformer': ('Conformer', 'conformer'),
        'onnxruntime': ('ONNX Runtime', 'onnxruntime'),
    }
    
    missing = []
    for module, (name, pip_name) in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ❌ {name} (pip install {pip_name})")
            missing.append(pip_name)
    
    if missing:
        print(f"\n❌ Missing dependencies. Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("✓ All dependencies installed")
    return True

def check_cosyvoice():
    """Check if CosyVoice2 can be imported"""
    print("\nChecking CosyVoice2 import...")
    try:
        from cosyvoice.cli.cosyvoice import CosyVoice2
        from cosyvoice.utils.file_utils import load_wav
        print("✓ CosyVoice2 can be imported")
        return True
    except ImportError as e:
        print(f"❌ Failed to import CosyVoice2: {e}")
        print("   Make sure you have installed all dependencies from requirements.txt")
        return False

def check_model_path():
    """Check if default model path exists"""
    print("\nChecking model path...")
    default_path = "pretrained_models/Cosyvoice2-Yue"
    
    if os.path.exists(default_path):
        print(f"✓ Default model path exists: {default_path}")
        # Check required files
        required_files = [
            'cosyvoice2.yaml',
            'campplus.onnx',
            'speech_tokenizer_v2.onnx',
            'spk2info.pt',
            'llm.pt',
            'flow.pt',
            'hift.pt'
        ]
        
        missing_files = []
        for f in required_files:
            if not os.path.exists(os.path.join(default_path, f)):
                missing_files.append(f)
        
        if missing_files:
            print(f"  ⚠️  Missing model files: {', '.join(missing_files)}")
            print(f"     The model will be downloaded from HuggingFace on first run.")
        else:
            print(f"  ✓ All model files present")
        return True
    else:
        print(f"⚠️  Default model path not found: {default_path}")
        print(f"   The model will be downloaded from HuggingFace on first run.")
        print(f"   Or download manually:")
        print(f"   python -c \"from huggingface_hub import snapshot_download; snapshot_download('ASLP-lab/WSYue-TTS', local_dir='pretrained_models')\"")
        return True  # Not a blocking issue, will download

def check_assets():
    """Check if reference audio files exist"""
    print("\nChecking reference audio files...")
    assets = [
        "asset/sg_017_090.wav",
        "asset/F01_中立_20054.wav"
    ]
    
    for asset in assets:
        if os.path.exists(asset):
            print(f"  ✓ {asset}")
        else:
            print(f"  ⚠️  {asset} not found")
    
    return True

def main():
    print("="*60)
    print("CosyVoice2-Yue OpenAI API Server Diagnostic")
    print("="*60)
    
    results = []
    results.append(("Python version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("CosyVoice2 import", check_cosyvoice()))
    results.append(("Model path", check_model_path()))
    results.append(("Assets", check_assets()))
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
        if not result:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✓ All checks passed! You can start the server with:")
        print("   python openai_server.py --port 8201")
    else:
        print("\n❌ Some checks failed. Please fix the issues above before starting the server.")
        sys.exit(1)

if __name__ == "__main__":
    main()
