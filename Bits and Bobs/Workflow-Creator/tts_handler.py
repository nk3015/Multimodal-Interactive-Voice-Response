import logging
import subprocess
from pathlib import Path
import torch
import numpy as np
import sounddevice as sd

class TTSHandler:
    def __init__(self):
        self.tts_engine = None
        try:
            # Import from local repository
            import sys
            repo_path = Path(__file__).parent / "kokoro-tts-repo"
            if repo_path.exists():
                sys.path.append(str(repo_path))
            
            from kokoro_tts import KokoroTTS
            model_path = self.find_model_path()
            voices_path = self.find_voices_path()
            
            if model_path and voices_path:
                self.tts_engine = KokoroTTS(
                    model_path=str(model_path),
                    voices_path=str(voices_path),
                    voice="af_sarah",
                    language="en-us"
                )
                logging.info("Kokoro TTS engine initialized successfully")
            else:
                logging.error("Kokoro TTS model files not found")
        except Exception as e:
            logging.error(f"Error initializing Kokoro TTS: {e}")

    def find_model_path(self):
        """Find Kokoro TTS model file"""
        possible_paths = [
            Path(__file__).parent / "kokoro-tts/kokoro-v1.0.onnx",
            Path(__file__).parent.parent / "kokoro-tts/kokoro-v1.0.onnx"
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return None

    def find_voices_path(self):
        """Find Kokoro TTS voices file"""
        possible_paths = [
            Path(__file__).parent / "kokoro-tts/voices-v1.0.bin",
            Path(__file__).parent.parent / "kokoro-tts/voices-v1.0.bin"
        ]
        for path in possible_paths:
            if path.exists():
                return path
        return None

    def speak(self, text, voice="af_sarah", speed=1.0):
        """Generate speech using Kokoro TTS"""
        if not self.tts_engine:
            logging.error("TTS engine not initialized")
            return

        try:
            # Generate audio
            audio = self.tts_engine.synthesize(
                text=text,
                voice=voice,
                speed=speed
            )
            
            # Play audio
            self.play_audio(audio)
            
        except Exception as e:
            logging.error(f"Error generating speech: {e}")

    def play_audio(self, audio_data):
        """Play audio using sounddevice"""
        try:
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
                
            # Play audio
            sd.play(audio_data, samplerate=22050)
            sd.wait()
            
        except Exception as e:
            logging.error(f"Error playing audio: {e}")