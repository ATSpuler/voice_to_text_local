# Voice-to-Text Local System

## Project Status: FULLY OPERATIONAL 

A distributed voice-to-text system using OpenAI Whisper with GPU acceleration.

## Architecture
- **Client (Mac)**: macOS 10.15.7, limited Homebrew support
- **Server (Ubuntu GPU)**: RTX 3060 12GB with nv-535 driver, running at 192.168.0.105:8000
- **Communication**: REST API over local network

## Hardware Setup
- Ubuntu GPU server: RTX 3060 12GB with existing nv-535 driver (preserved)
- Mac client: Intel Mac, macOS 10.15.7 (limited package management)
- Network: Direct SSH access via 192.168.0.105

## Current Implementation

### Working Files
- `server.py`: FastAPI server with Whisper integration (CUDA-enabled)
- `client_simple.py`: macOS-compatible client (no PyAudio dependency)
- `setup_server_fixed.sh`: Safe setup script (preserves existing drivers)
- `pyproject.toml`: Project dependencies

### Discarded Files (moved to discarded/)
- `client.py`: Full-featured client requiring PyAudio compilation
- `setup_server_safe.sh`: Earlier version of setup script

## Server Setup Completed
- Python virtual environment created at `/home/al/voice_to_text_local/venv`
- PyTorch 2.7.1+cu118 with CUDA support verified
- Whisper base model configured for RTX 3060
- All dependencies installed successfully
- GPU testing confirmed: "NVIDIA GeForce RTX 3060" accessible

## Client Setup Completed
- Simple client works without PyAudio compilation issues
- Uses system tools for audio recording when available
- File upload option for testing
- Successfully connects to server at http://192.168.0.105:8000

## Current Workflow

### Start Server (Ubuntu)
```bash
ssh al@192.168.0.105
cd voice_to_text_local
source venv/bin/activate
python server.py
```

### Start Client (Mac)
```bash
cd /Volumes/Macintosh\ HD/Users/sanchez/2025/scratch/voice_to_text_local
python client_simple.py
# Enter: http://192.168.0.105:8000
# Commands: 'r' record, 'f' file, 't' test, 'q' quit
```

## Technical Details
- Audio format: 16-bit PCM, mono, 16kHz (Whisper optimal)
- Whisper model: 'base' (suitable for 12GB VRAM)
- API endpoints: `/` (health), `/transcribe` (main), `/model-info`
- Temp file handling with proper cleanup
- CORS enabled for cross-origin requests

## Remaining Tasks
- [ ] Add real-time audio streaming capabilities
- [ ] Test end-to-end system optimization
- [ ] Optional: SSH tunnel or API authentication

## Last Session Result
System tested successfully - server running with GPU acceleration, client connecting and ready for transcription. All core functionality operational.