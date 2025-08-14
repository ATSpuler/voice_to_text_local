# Voice-to-Text Local System

Distributed voice-to-text system using OpenAI Whisper with GPU acceleration.

## Architecture

- **Server**: Ubuntu with RTX 3060 GPU (192.168.0.105:8000)
- **Client**: macOS 10.15.7 with FFmpeg audio recording
- **API**: REST endpoints for transcription

## Quick Start

### Server (Ubuntu GPU)
```bash
ssh al@192.168.0.105
cd voice_to_text_local
source venv/bin/activate
python server.py
```

### Client (Mac)

**Interactive Mode:**
```bash
python client_simple.py
# Commands: 'r' record, 'f' file, 'h' history, 't' test, 'q' quit
```

**Streaming Mode:**
```bash
python client_streaming.py
# Commands: 's' start streaming, 'o' view output, 't' test, 'q' quit
```

## Features

- GPU-accelerated Whisper transcription (large model)
- Real microphone recording via FFmpeg
- Multi-language support (auto-detection)
- No PyAudio dependency on client
- Temporary file handling with cleanup
- **NEW**: Streaming continuous transcription
- **NEW**: APSW SQLite database storage
- **NEW**: Clean text output to files

## Requirements

- **Server**: Python 3.9+, CUDA-enabled GPU
- **Client**: Python 3.9+, FFmpeg for audio recording, APSW

## Client Features

### Interactive Mode (`client_simple.py`)
- One-time recordings
- File transcription
- Transcription history viewing
- Database storage with timestamps

### Streaming Mode (`client_streaming.py`)
- Continuous recording in configurable chunks (default: 5s)
- Real-time transcription output
- Clean text output to file (`live_transcription.txt`)
- Database storage with full metadata
- Graceful shutdown with processing completion

## Known Issues

- **Longer chunks** (10-20s): May lose final portion of speech due to processing timeout
- **Recommendation**: Use 5-second chunks for best results

## API Endpoints

- `GET /` - Health check
- `POST /transcribe` - Audio transcription
- `GET /model-info` - Model status