# Requirements

```
# Core dependencies
PyQt6==6.5.0
PyQt6-WebEngine==6.5.0
numpy==1.24.3
sounddevice==0.4.6
soundfile==0.12.1
pathlib==1.0.1
requests==2.31.0

# AI and speech processing
ollama==0.1.5  # Optional, needed for AI capabilities
SpeechRecognition==3.10.0
pyaudio==0.2.13

# Optional: Text-to-speech capabilities
TTS==0.17.5
torch==2.0.1

# Optional: Enhanced web scraping and data handling
beautifulsoup4==4.12.2
markdown==3.4.3
pandas==2.0.3
pyarrow==12.0.1
```

## Installation Instructions

### Basic Installation

To install the core dependencies:

```bash
pip install -r requirements.txt
```

### Audio Dependencies

PyAudio may require additional system packages:

#### Linux (Debian/Ubuntu):
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

#### macOS:
```bash
brew install portaudio
```

#### Windows:
PyAudio should install without additional steps on Windows through pip.

### Ollama Setup

To use the AI capabilities, you'll need to install and set up Ollama:

1. Visit [ollama.ai](https://ollama.ai) or [github.com/ollama/ollama](https://github.com/ollama/ollama) to download Ollama
2. Start the Ollama service:
   ```bash
   ollama serve
   ```
3. Pull a model (llama3 is recommended):
   ```bash
   ollama pull llama3
   ```

### TTS Setup

For text-to-speech support:

```bash
pip install TTS
```

Note: The TTS package will download models on first use.
