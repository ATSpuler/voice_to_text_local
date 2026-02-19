#!/usr/bin/env python3
"""
Simple Voice-to-Text Client for macOS 10.15.7
Uses system audio recording instead of PyAudio
"""

import subprocess
import requests
import tempfile
import os
import time
import apsw
import datetime
from typing import Optional, List, Tuple

class SimpleVoiceClient:
    def __init__(self, server_url: str = "http://localhost:8000", db_path: str = "transcriptions.db"):
        self.server_url = server_url.rstrip('/')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize APSW database for storing transcriptions"""
        db = apsw.Connection(self.db_path)
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                text TEXT NOT NULL,
                language TEXT,
                duration INTEGER,
                source TEXT DEFAULT 'recording'
            )
        ''')
        db.close()
    
    def save_transcription(self, text: str, language: str = "unknown", duration: int = None, source: str = "recording"):
        """Save transcription to database"""
        db = apsw.Connection(self.db_path)
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (text, language, duration, source)
            VALUES (?, ?, ?, ?)
        ''', (text, language, duration, source))
        db.close()
    
    def get_transcriptions(self, limit: int = 20) -> List[Tuple]:
        """Get recent transcriptions from database"""
        db = apsw.Connection(self.db_path)
        cursor = db.cursor()
        results = list(cursor.execute('''
            SELECT id, timestamp, text, language, duration, source
            FROM transcriptions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,)))
        db.close()
        return results
        
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
    
    def record_audio_system(self, duration: int = 5) -> str:
        """Record audio using macOS system command"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()
        
        print(f"🎤 Recording for {duration} seconds using system audio...")
        
        # Use macOS built-in audio recording
        cmd = [
            'rec', '-r', '16000', '-c', '1', temp_file.name,
            'trim', '0', str(duration)
        ]
        
        try:
            # Try sox first
            subprocess.run(cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to ffmpeg if available
            try:
                cmd = [
                    'ffmpeg', '-f', 'avfoundation', '-i', ':0',
                    '-ar', '16000', '-ac', '1', '-t', str(duration),
                    '-y', temp_file.name
                ]
                print("🎤 Using FFmpeg to record from Built-in Microphone...")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Last resort: use system say to create test audio
                print("⚠️  No audio recording tools found. Creating test audio...")
                cmd = [
                    'say', '-o', temp_file.name.replace('.wav', '.aiff'),
                    'This is a test recording for voice to text'
                ]
                subprocess.run(cmd, check=True)
                
                # Convert AIFF to WAV if possible
                try:
                    convert_cmd = [
                        'ffmpeg', '-i', temp_file.name.replace('.wav', '.aiff'),
                        '-ar', '16000', '-ac', '1', temp_file.name
                    ]
                    subprocess.run(convert_cmd, check=True, capture_output=True)
                    os.unlink(temp_file.name.replace('.wav', '.aiff'))
                except:
                    # Just rename the AIFF file
                    os.rename(temp_file.name.replace('.wav', '.aiff'), temp_file.name)
        
        print("✅ Recording completed")
        return temp_file.name
    
    def record_from_file(self, file_path: str) -> str:
        """Use an existing audio file for testing"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        return file_path
    
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
                return text, language
            else:
                print(f"❌ Transcription failed: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def interactive_mode(self):
        """Interactive mode with simplified recording"""
        print("🎙️  Simple Voice-to-Text Client (macOS 10.15.7)")
        print("Commands:")
        print("  'r' = record audio")
        print("  'f' = transcribe file") 
        print("  'h' = view transcription history")
        print("  't' = test server")
        print("  'q' = quit")
        
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
                
                try:
                    audio_file = self.record_audio_system(duration)
                    result = self.transcribe_file(audio_file)
                    if result:
                        text, language = result
                        print(f"📝 Transcription: '{text}'")
                        self.save_transcription(text, language, duration, "recording")
                        print("💾 Saved to database")
                    else:
                        print("❌ Transcription failed")
                    
                    # Clean up
                    if os.path.exists(audio_file):
                        os.unlink(audio_file)
                except Exception as e:
                    print(f"❌ Recording failed: {e}")
                    
            elif command == 'f':
                file_path = input("Enter audio file path: ").strip()
                result = self.transcribe_file(file_path)
                if result:
                    text, language = result
                    print(f"📝 Transcription: '{text}'")
                    self.save_transcription(text, language, None, f"file:{os.path.basename(file_path)}")
                    print("💾 Saved to database")
                else:
                    print("❌ Transcription failed")
            elif command == 'h':
                print("\n📚 Recent Transcriptions:")
                transcriptions = self.get_transcriptions()
                if not transcriptions:
                    print("No transcriptions found.")
                else:
                    for i, (id, timestamp, text, language, duration, source) in enumerate(transcriptions[:10]):
                        print(f"{i+1}. [{timestamp}] ({language}) {source}: {text[:50]}{'...' if len(text) > 50 else ''}")
            else:
                print("Unknown command. Use 'r', 'f', 'h', 't', or 'q'")

def main():
    print("Simple Voice-to-Text Client for macOS 10.15.7")
    print("This version works without PyAudio compilation issues")
    
    server_url = input("Server URL (default: http://100.107.71.56:8000): ").strip()
    if not server_url:
        server_url = "http://100.107.71.56:8000"
    
    client = SimpleVoiceClient(server_url)
    
    # Test server first
    if not client.test_server_connection():
        print("Cannot connect to server. Make sure:")
        print("1. Server is running: ssh al@100.107.71.56")
        print("2. Run: cd voice_to_text_local && source venv/bin/activate && python server.py")
        return
    
    client.interactive_mode()
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()