#!/usr/bin/env python3
"""
Voice-to-Text Client (Mac)
Records audio and sends to Ubuntu GPU server for transcription
"""

import pyaudio
import wave
import requests
import tempfile
import os
import threading
import time
from typing import Optional

class VoiceClient:
    def __init__(self, server_url: str = "http://localhost:8000"):
        self.server_url = server_url.rstrip('/')
        self.is_recording = False
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000  # Whisper optimal sample rate
        self.chunk = 1024
        self.audio = pyaudio.PyAudio()
        
    def test_server_connection(self) -> bool:
        """Test connection to the server"""
        try:
            response = requests.get(f"{self.server_url}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server connected: {data}")
                return True
            else:
                print(f"❌ Server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def record_audio(self, duration: int = 5) -> str:
        """Record audio for specified duration and save to temp file"""
        print(f"🎤 Recording for {duration} seconds...")
        
        stream = self.audio.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        frames = []
        for _ in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
        
        print("✅ Recording completed")
        return temp_file.name
    
    def transcribe_file(self, audio_file_path: str) -> Optional[str]:
        """Send audio file to server for transcription"""
        try:
            print("📤 Sending audio to server...")
            
            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio': ('audio.wav', audio_file, 'audio/wav')}
                response = requests.post(
                    f"{self.server_url}/transcribe",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                language = result.get('language', 'unknown')
                print(f"🌍 Detected language: {language}")
                return text
            else:
                print(f"❌ Transcription failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def record_and_transcribe(self, duration: int = 5) -> Optional[str]:
        """Record audio and get transcription"""
        audio_file = None
        try:
            # Record audio
            audio_file = self.record_audio(duration)
            
            # Transcribe
            text = self.transcribe_file(audio_file)
            
            return text
        finally:
            # Clean up temp file
            if audio_file and os.path.exists(audio_file):
                os.unlink(audio_file)
    
    def interactive_mode(self):
        """Interactive recording mode"""
        print("🎙️  Voice-to-Text Client")
        print("Commands: 'r' = record, 'q' = quit, 't' = test server")
        
        while True:
            command = input("\n> ").strip().lower()
            
            if command == 'q':
                break
            elif command == 't':
                self.test_server_connection()
            elif command == 'r':
                duration = input("Recording duration (seconds, default 5): ").strip()
                try:
                    duration = int(duration) if duration else 5
                except ValueError:
                    duration = 5
                
                text = self.record_and_transcribe(duration)
                if text:
                    print(f"📝 Transcription: '{text}'")
                else:
                    print("❌ Transcription failed")
            else:
                print("Unknown command. Use 'r', 't', or 'q'")
    
    def cleanup(self):
        """Clean up audio resources"""
        self.audio.terminate()

def main():
    # Default to localhost, but can be changed for SSH tunnel or direct IP
    server_url = input("Server URL (default: http://localhost:8000): ").strip()
    if not server_url:
        server_url = "http://localhost:8000"
    
    client = VoiceClient(server_url)
    
    try:
        # Test server connection first
        if not client.test_server_connection():
            print("Cannot connect to server. Make sure the server is running.")
            return
        
        # Start interactive mode
        client.interactive_mode()
        
    finally:
        client.cleanup()
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()