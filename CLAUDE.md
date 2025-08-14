# Voice-to-Text Local System

## Project Status: FULLY OPERATIONAL + STREAMING 

A distributed voice-to-text system using OpenAI Whisper with GPU acceleration and streaming capabilities.

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
- `server.py`: FastAPI server with Whisper integration (CUDA-enabled, large model)
- `client_simple.py`: macOS-compatible client (no PyAudio dependency, APSW database)
- `client_streaming.py`: Continuous streaming transcription client
- `setup_server_fixed.sh`: Safe setup script (preserves existing drivers)
- `pyproject.toml`: Project dependencies (includes APSW)

### Discarded Files (moved to discarded/)
- `client.py`: Full-featured client requiring PyAudio compilation
- `setup_server_safe.sh`: Earlier version of setup script

## Server Setup Completed
- Python virtual environment created at `/home/al/voice_to_text_local/venv`
- PyTorch 2.7.1+cu118 with CUDA support verified
- Whisper large model configured for RTX 3060 (upgraded from base)
- All dependencies installed successfully
- GPU testing confirmed: "NVIDIA GeForce RTX 3060" accessible

## Client Setup Completed
- Interactive client (`client_simple.py`) works without PyAudio compilation issues
- Streaming client (`client_streaming.py`) for continuous transcription
- APSW SQLite database for transcription storage
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

**Interactive Mode:**
```bash
cd /Volumes/Macintosh\ HD/Users/sanchez/2025/scratch/voice_to_text_local
python client_simple.py
# Enter: http://192.168.0.105:8000
# Commands: 'r' record, 'f' file, 'h' history, 't' test, 'q' quit
```

**Streaming Mode:**
```bash
python client_streaming.py
# Enter: http://192.168.0.105:8000
# Commands: 's' start streaming, 'o' view output, 't' test, 'q' quit
```

## Real Audio Recording Setup (COMPLETED)
- **FFmpeg installed**: Version 5.1.2-tessus working on macOS 10.15.7
- **Microphone access**: "Built-in Microphone" device detected and functional
- **Recording command**: `ffmpeg -f avfoundation -i :0 -ar 16000 -ac 1 -t [duration] output.wav`
- **Status**: Real voice recording working, no more mock audio

## Technical Details
- Audio format: 16-bit PCM, mono, 16kHz (Whisper optimal)
- Whisper model: 'large' (optimized for 12GB VRAM, upgraded from base)
- API endpoints: `/` (health), `/transcribe` (main), `/model-info`
- Temp file handling with proper cleanup
- CORS enabled for cross-origin requests
- Database: APSW SQLite for transcription storage
- Streaming: Configurable chunk duration (default 5s, supports 3-20s)

## Completed Features
- ✅ Real-time audio streaming capabilities (client_streaming.py)
- ✅ APSW SQLite database storage
- ✅ Clean text output to files
- ✅ Graceful shutdown with processing completion
- ✅ Whisper large model integration

## Known Issues
- **Longer chunks (10-20s)**: May lose final portion due to processing timeout
- **Recommendation**: Use 5-second chunks for optimal results

## Optional Future Enhancements
- [ ] SSH tunnel or API authentication
- [ ] Voice activity detection to skip silence

## Testing Results
✅ **Multi-language transcription confirmed**:
- English example: "Hola, how are you? What would you like to tell me? Tell me now Tell me" 
- Spanish example: "Hola papanatas, ¿cómo estás papanatas? Dime algo papanatas."
- Language auto-detection working (en/es)

## File Storage Behavior  
- **Audio files**: NOT saved (deleted after transcription for privacy)
- **Transcriptions**: SAVED to APSW SQLite database with full metadata
- **Streaming output**: Clean text saved to configurable output file
- **Server logs**: No persistent storage

## Session Status
✅ FULLY OPERATIONAL + STREAMING - Real microphone recording with GPU-accelerated transcription
- Real-time voice capture via FFmpeg
- Multi-language support confirmed  
- Client-server communication stable
- Streaming transcription with database storage
- Clean text output for continuous recording
- All originally planned features completed + streaming enhancements