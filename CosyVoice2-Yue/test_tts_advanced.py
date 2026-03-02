#!/usr/bin/env python3
"""
Advanced testing program for CosyVoice2-Yue with voice quality options.
"""

import sys
import os
import argparse

sys.path.append('third_party/Matcha-TTS')

try:
    import hyperpyyaml
except ImportError as e:
    print("Error: 'hyperpyyaml' is not installed. Run: pip install 'ruamel.yaml>=0.17.28,<0.18' --force-reinstall")
    sys.exit(1)

from cosyvoice.cli.cosyvoice import CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import torch

try:
    import opencc
    OPENCC_AVAILABLE = True
except ImportError:
    OPENCC_AVAILABLE = False


def load_model(model_path, load_jit=False, load_trt=False, load_vllm=False, fp16=False):
    """Load a CosyVoice2 model."""
    import warnings
    warnings.filterwarnings('ignore')
    
    print(f"Loading model from: {model_path}")
    model = CosyVoice2(
        model_path,
        load_jit=load_jit,
        load_trt=load_trt,
        load_vllm=load_vllm,
        fp16=fp16
    )
    print(f"Model loaded. Sample rate: {model.sample_rate}")
    return model


def synthesize(model, text, instruct_text, prompt_speech, output_file, stream=False, speed=1.0):
    """Synthesize speech and save to file."""
    print(f"\nSynthesizing:")
    print(f"  Text: {text}")
    print(f"  Instruct: {instruct_text}")
    print(f"  Speed: {speed}x")
    
    for i, output in enumerate(model.inference_instruct2(text, instruct_text, prompt_speech, stream=stream, speed=speed)):
        torchaudio.save(output_file, output['tts_speech'], model.sample_rate)
        print(f"  Saved: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description='Advanced CosyVoice2-Yue TTS testing')
    parser.add_argument('--model', type=str, required=True, help='Model path')
    parser.add_argument('--prompt', type=str, required=True, help='Prompt audio file')
    parser.add_argument('--text', type=str, required=True, help='Text to synthesize')
    parser.add_argument('--instruct', type=str, default='用粤语说这句话', help='Instruction')
    parser.add_argument('--output', type=str, default='output.wav', help='Output file')
    parser.add_argument('--speed', type=float, default=1.0, help='Speech speed (0.5-2.0)')
    parser.add_argument('--fp16', action='store_true', help='Use FP16')
    parser.add_argument('--convert-s2t', action='store_true', help='Convert S2T Chinese')
    
    args = parser.parse_args()
    
    # Text conversion
    text = args.text
    if args.convert_s2t and OPENCC_AVAILABLE:
        converter = opencc.OpenCC('s2t.json')
        text = converter.convert(text)
        print(f"Converted: {text}")
    
    # Load prompt
    print(f"Loading prompt: {args.prompt}")
    prompt_speech = load_wav(args.prompt, 16000)
    print(f"Prompt shape: {prompt_speech.shape}")
    
    # Load model
    model = load_model(args.model, fp16=args.fp16)
    
    # Synthesize
    synthesize(model, text, args.instruct, prompt_speech, args.output, speed=args.speed)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
