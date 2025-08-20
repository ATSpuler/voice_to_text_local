#!/usr/bin/env python3
"""
Simple Toggle Voice-to-Text Client
Terminal-only, no permissions needed
"""

import subprocess
import requests
import tempfile
import os
import time
import apsw
import datetime
import termios
import tty
import sys
import signal
from typing import Optional, Tuple

class SimpleToggleClient:
    def __init__(self, server_url: str = "http://192.168.0.105:8000", db_path: str = "transcriptions.db"):
        self.server_url = server_url.rstrip('/')
        self.db_path = db_path
        self.is_recording = False
        self.recording_process = None
        self.current_audio_file = None
        self.last_key_time = 0
        self.init_database()
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down...")
        self.cleanup_recording()
        sys.exit(0)
    
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
                source TEXT DEFAULT 'toggle'
            )
        ''')
        db.close()
    
    def save_transcription(self, text: str, language: str = "unknown", duration: int = None):
        """Save transcription to database"""
        db = apsw.Connection(self.db_path)
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO transcriptions (text, language, duration, source)
            VALUES (?, ?, ?, ?)
        ''', (text, language, duration, "toggle"))
        db.close()
    
    def copy_to_clipboard(self, text: str):
        """Copy text to macOS clipboard using pbcopy"""
        try:
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=text)
            if process.returncode == 0:
                return True
            else:
                print(f"❌ pbcopy failed with return code {process.returncode}")
                return False
        except Exception as e:
            print(f"❌ Clipboard error: {e}")
            return False
    
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
    
    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        self.current_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        self.current_audio_file.close()
        
        cmd = [
            'ffmpeg', '-f', 'avfoundation', '-i', ':0',
            '-ar', '16000', '-ac', '1',
            '-y', self.current_audio_file.name
        ]
        
        try:
            self.recording_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.is_recording = True
            print("🎤 RECORDING... (press 'c' to stop)")
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            if os.path.exists(self.current_audio_file.name):
                os.unlink(self.current_audio_file.name)
            self.current_audio_file = None
    
    def stop_recording(self):
        """Stop recording and process audio"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if self.recording_process:
            try:
                self.recording_process.terminate()
                self.recording_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.recording_process.kill()
                self.recording_process.wait()
            except Exception as e:
                print(f"❌ Error stopping recording: {e}")
        
        print("🔄 Processing...")
        
        if self.current_audio_file and os.path.exists(self.current_audio_file.name):
            # Check if file has content
            if os.path.getsize(self.current_audio_file.name) > 1000:  # At least 1KB
                result = self.transcribe_file(self.current_audio_file.name)
                if result:
                    text, language = result
                    if len(text.strip()) > 2:
                        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                        print(f"📝 [{timestamp}] ({language}): {text}")
                        
                        self.save_transcription(text, language)
                        self.copy_to_clipboard(text)
                        print("📋 Copied to clipboard")
                    else:
                        print("⚠️ Transcription too short, skipped")
                else:
                    print("❌ Transcription failed")
            else:
                print("⚠️ Recording too short, skipped")
            
            # Cleanup
            os.unlink(self.current_audio_file.name)
        
        self.current_audio_file = None
        self.recording_process = None
        print("✅ Ready (press 'c' to start recording)")
    
    def cleanup_recording(self):
        """Clean up any ongoing recording"""
        if self.is_recording:
            self.stop_recording()
    
    def transcribe_file(self, audio_file_path: str) -> Optional[Tuple[str, str]]:
        """Send audio file to server for transcription"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                files = {'audio': ('audio.wav', audio_file, 'audio/wav')}
                response = requests.post(
                    f"{self.server_url}/transcribe",
                    files=files,
                    timeout=15
                )
            
            if response.status_code == 200:
                result = response.json()
                text = result.get('text', '').strip()
                language = result.get('language', 'unknown')
                return text, language
            else:
                print(f"❌ Transcription failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error: {e}")
            return None
    
    def get_char(self):
        """Get a single character from terminal without Enter"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char
    
    def run(self):
        """Run the toggle client"""
        if not self.test_server_connection():
            print("Cannot connect to server. Make sure:")
            print("1. Server is running: ssh al@192.168.0.105")
            print("2. Run: cd voice_to_text_local && source venv/bin/activate && python server.py")
            return
        
        print("🎙️ Simple Toggle Voice-to-Text Client")
        print("📋 Text will be automatically copied to clipboard")
        print("⌨️ Press 'c' to start recording, press 'c' again to stop & transcribe")
        print("🚪 Press 'q' to quit")
        print("✅ Ready (press 'c' to start recording)")
        
        while True:
            try:
                char = self.get_char().lower()
                
                if char == 'c':
                    current_time = time.time()
                    if current_time - self.last_key_time > 0.5:  # 500ms debounce
                        self.last_key_time = current_time
                        if not self.is_recording:
                            self.start_recording()
                        else:
                            self.stop_recording()
                elif char == 'q':
                    print("\n👋 Goodbye!")
                    self.cleanup_recording()
                    break
                elif char == '\x03':  # Ctrl+C
                    print("\n👋 Goodbye!")
                    self.cleanup_recording()
                    break
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                self.cleanup_recording()
                break

def main():
    print("Simple Toggle Voice-to-Text Client")
    print("Press 'c' to toggle recording, no permissions needed!")
    
    server_url = input("Server URL (default: http://192.168.0.105:8000): ").strip()
    if not server_url:
        server_url = "http://192.168.0.105:8000"
    
    client = SimpleToggleClient(server_url)
    client.run()

if __name__ == "__main__":
    main()