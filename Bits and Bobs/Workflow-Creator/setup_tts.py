import subprocess
import sys
import os
from pathlib import Path

def setup_kokoro_tts():
    """Setup Kokoro TTS and download required models"""
    print("Setting up Kokoro TTS...")
    
    # Create models directory
    models_dir = Path(__file__).parent / "kokoro-tts"
    models_dir.mkdir(exist_ok=True)
    
    # Clone Kokoro TTS repository if not present
    repo_dir = Path(__file__).parent / "kokoro-tts-repo"
    if not repo_dir.exists():
        print("Cloning Kokoro TTS repository...")
        subprocess.run([
            "git", "clone", 
            "https://github.com/nazdridoy/kokoro-tts.git",
            str(repo_dir)
        ])
    
    # Install requirements
    requirements_file = repo_dir / "requirements.txt"
    if requirements_file.exists():
        print("Installing requirements...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", str(requirements_file)
        ])
    
    # Install Kokoro TTS in development mode
    print("Installing Kokoro TTS...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", "-e", str(repo_dir)
    ])
    
    # Download model files using curl/powershell
    model_path = models_dir / "kokoro-v1.0.onnx"
    voices_path = models_dir / "voices-v1.0.bin"
    
    if not model_path.exists():
        print("Downloading Kokoro TTS model...")
        subprocess.run([
            "powershell",
            "-Command",
            f"Invoke-WebRequest -Uri 'https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx' -OutFile '{str(model_path)}'"
        ])
    
    if not voices_path.exists():
        print("Downloading voice data...")
        subprocess.run([
            "powershell",
            "-Command",
            f"Invoke-WebRequest -Uri 'https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin' -OutFile '{str(voices_path)}'"
        ])
    
    print("Kokoro TTS setup complete!")

if __name__ == "__main__":
    setup_kokoro_tts()