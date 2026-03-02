#!/usr/bin/env python3
"""
Example client for OpenAI API Compatible CosyVoice2-Yue Server
Demonstrates how to use the API with the OpenAI Python client or raw HTTP requests.
"""

import os
import sys
import argparse
import base64


def synthesize_openai_sdk(text: str, voice: str = "alloy", output_file: str = "output.mp3", 
                          server_url: str = "http://localhost:8201"):
    """
    Synthesize speech using the OpenAI Python SDK.
    Note: This requires the OpenAI Python package: pip install openai
    """
    try:
        from openai import OpenAI
    except ImportError:
        print("OpenAI package not installed. Install with: pip install openai")
        print("Falling back to raw HTTP request...")
        return synthesize_raw_http(text, voice, output_file, server_url)
    
    # Create client pointing to our local server
    client = OpenAI(
        base_url=f"{server_url}/v1",
        api_key="dummy-api-key"  # Not used but required by SDK
    )
    
    print(f"Synthesizing: '{text[:50]}...' with voice '{voice}'")
    
    # Call the TTS API
    response = client.audio.speech.create(
        model="cosyvoice2-yue",
        voice=voice,
        input=text,
        response_format="mp3"
    )
    
    # Save the audio
    response.stream_to_file(output_file)
    print(f"Audio saved to: {output_file}")
    return output_file


def synthesize_raw_http(text: str, voice: str = "alloy", output_file: str = "output.mp3",
                        server_url: str = "http://localhost:8201"):
    """
    Synthesize speech using raw HTTP requests.
    This doesn't require the OpenAI package.
    """
    import requests
    
    url = f"{server_url}/v1/audio/speech"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-api-key"
    }
    
    data = {
        "model": "cosyvoice2-yue",
        "input": text,
        "voice": voice,
        "response_format": output_file.split(".")[-1] if "." in output_file else "mp3"
    }
    
    print(f"Synthesizing: '{text[:50]}...' with voice '{voice}'")
    print(f"Request to: {url}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to: {output_file}")
        return output_file
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def synthesize_with_custom_voice(text: str, prompt_audio_path: str, output_file: str = "output.mp3",
                                 server_url: str = "http://localhost:8201"):
    """
    Synthesize speech with a custom voice using a reference audio file.
    """
    import requests
    
    url = f"{server_url}/v1/audio/speech"
    
    # Read and encode the prompt audio
    with open(prompt_audio_path, "rb") as f:
        audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer dummy-api-key"
    }
    
    data = {
        "model": "cosyvoice2-yue",
        "input": text,
        "voice": "custom",  # Voice name is ignored when prompt_audio is provided
        "response_format": output_file.split(".")[-1] if "." in output_file else "mp3",
        "prompt_audio": audio_b64  # Base64-encoded audio
    }
    
    print(f"Synthesizing: '{text[:50]}...' with custom voice from: {prompt_audio_path}")
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to: {output_file}")
        return output_file
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def list_voices(server_url: str = "http://localhost:8201"):
    """List available voices on the server."""
    import requests
    
    url = f"{server_url}/v1/voices"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("Available voices:")
        for voice, info in data["voices"].items():
            status = "✓" if info["exists"] else "✗"
            print(f"  {status} {voice}: {info['path']}")
        print(f"\nDefault instruction: {data['default_instruct']}")
    else:
        print(f"Error: {response.status_code}")


def health_check(server_url: str = "http://localhost:8201"):
    """Check server health."""
    import requests
    
    url = f"{server_url}/health"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Server status: {data['status']}")
        print(f"Model loaded: {data['model_loaded']}")
        print(f"Sample rate: {data['sample_rate']}")
    else:
        print(f"Error: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(
        description="Example client for CosyVoice2-Yue OpenAI API Server"
    )
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:8201",
        help="Server URL"
    )
    parser.add_argument(
        "--text",
        type=str,
        default="收到朋友从远方寄嚟嘅生日礼物，嗰份意外嘅惊喜同埋深深嘅祝福令我心入面充满咗甜蜜嘅快乐。",
        help="Text to synthesize"
    )
    parser.add_argument(
        "--voice",
        type=str,
        default="alloy",
        help="Voice to use"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output.mp3",
        help="Output audio file"
    )
    parser.add_argument(
        "--prompt-audio",
        type=str,
        default=None,
        help="Path to custom prompt audio for voice cloning"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=["synthesize", "list-voices", "health"],
        default="synthesize",
        help="Action to perform"
    )
    parser.add_argument(
        "--use-openai-sdk",
        action="store_true",
        help="Use OpenAI SDK instead of raw HTTP"
    )
    
    args = parser.parse_args()
    
    if args.action == "health":
        health_check(args.server)
    elif args.action == "list-voices":
        list_voices(args.server)
    elif args.action == "synthesize":
        if args.prompt_audio:
            synthesize_with_custom_voice(args.text, args.prompt_audio, args.output, args.server)
        elif args.use_openai_sdk:
            synthesize_openai_sdk(args.text, args.voice, args.output, args.server)
        else:
            synthesize_raw_http(args.text, args.voice, args.output, args.server)


if __name__ == "__main__":
    main()
