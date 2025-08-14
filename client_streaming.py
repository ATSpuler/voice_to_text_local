#!/usr/bin/env python3
"""
Streaming Voice-to-Text Client
Continuous recording, processing, and text output
"""

import subprocess
import requests
import tempfile
import os
import time
import threading
import apsw
import datetime
from typing import Optional
import signal
import sys
import queue

class StreamingVoiceClient:
    def __init__(self, server_url: str = "http://192.168.0.105:8000", 
                 chunk_duration: int = 5, output_file: str = "live_transcription.txt"):
        self.server_url = server_url.rstrip('/')
        self.chunk_duration = chunk_duration
        self.output_file = output_file
        self.db_path = "transcriptions.db"
        self.recording = False
        self.audio_queue = queue.Queue()
        self.init_database()
        
        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Stopping streaming... waiting for processing to complete...")
        self.recording = False
        # Don't exit immediately - let streaming_mode handle cleanup
    
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
                source TEXT DEFAULT 'streaming'
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
        ''', (text, language, duration, "streaming"))
        db.close()
    
    def append_to_file(self, text: str, language: str = "unknown"):
        """Append transcription to output file as clean text"""
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(f"{text} ")
            f.flush()
    
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
    
    def record_audio_chunk(self) -> Optional[str]:
        """Record a single audio chunk"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.close()
        
        cmd = [
            'ffmpeg', '-f', 'avfoundation', '-i', ':0',
            '-ar', '16000', '-ac', '1', '-t', str(self.chunk_duration),
            '-y', temp_file.name
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return temp_file.name
            else:
                print(f"❌ Recording failed: {result.stderr}")
                os.unlink(temp_file.name)
                return None
        except Exception as e:
            print(f"❌ Recording error: {e}")
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            return None
    
    def transcribe_file(self, audio_file_path: str) -> Optional[tuple]:
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
    
    def audio_recorder(self):
        """Continuous audio recording thread"""
        print("🎤 Recording thread started")
        while self.recording:
            audio_file = self.record_audio_chunk()
            if audio_file:
                self.audio_queue.put(audio_file)
            else:
                time.sleep(1)
        print("🎤 Recording thread stopped")
    
    def audio_processor(self):
        """Continuous audio processing thread"""
        print("🔄 Processing thread started")
        while self.recording:
            try:
                audio_file = self.audio_queue.get(timeout=1)
                self.process_audio_chunk(audio_file)
            except queue.Empty:
                continue
        
        # Process remaining items in queue
        while not self.audio_queue.empty():
            try:
                audio_file = self.audio_queue.get_nowait()
                self.process_audio_chunk(audio_file)
            except queue.Empty:
                break
        print("🔄 Processing thread stopped")
    
    def process_audio_chunk(self, audio_file: str):
        """Process a single audio chunk"""
        if not audio_file or not os.path.exists(audio_file):
            return
            
        result = self.transcribe_file(audio_file)
        if result:
            text, language = result
            
            # Skip if transcription is empty or too short
            if len(text.strip()) < 3:
                os.unlink(audio_file)
                return
            
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            print(f"📝 [{timestamp}] ({language}): {text}")
            
            # Save to database and file
            self.save_transcription(text, language, self.chunk_duration)
            print("💾 Saved to database")
            self.append_to_file(text, language)
        
        # Clean up
        os.unlink(audio_file)
    
    def streaming_mode(self):
        """Start continuous streaming transcription"""
        print(f"🎙️  Starting streaming transcription...")
        print(f"📁 Output file: {self.output_file}")
        print(f"⏱️  Chunk duration: {self.chunk_duration} seconds")
        print(f"🛑 Press Ctrl+C to stop\n")
        
        # Clear output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("")  # Start with clean file
        
        self.recording = True
        
        # Start threads
        recorder_thread = threading.Thread(target=self.audio_recorder, daemon=True)
        processor_thread = threading.Thread(target=self.audio_processor, daemon=True)
        
        recorder_thread.start()
        processor_thread.start()
        
        try:
            # Keep main thread alive
            while self.recording:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping...")
        finally:
            self.recording = False
            
            print("⏳ Stopping recording...")
            recorder_thread.join(timeout=2)
            
            # Check how many chunks are left to process
            remaining = self.audio_queue.qsize()
            if remaining > 0:
                print(f"⏳ Processing {remaining} remaining chunks (max 10s each)...")
                processor_thread.join(timeout=max(10, remaining * 10))
            else:
                processor_thread.join(timeout=2)
            
            # Add final newline to file
            with open(self.output_file, 'a', encoding='utf-8') as f:
                f.write("\n")
    
    def interactive_mode(self):
        """Interactive mode for streaming control"""
        print("🎙️  Streaming Voice-to-Text Client")
        print("Commands:")
        print("  's' = start streaming")
        print("  'o' = view output file")
        print("  't' = test server")
        print("  'q' = quit")
        
        while True:
            command = input("\n> ").strip().lower()
            
            if command == 'q':
                break
            elif command == 't':
                self.test_server_connection()
            elif command == 's':
                if not self.test_server_connection():
                    print("❌ Cannot start streaming - server not available")
                    continue
                self.streaming_mode()
            elif command == 'o':
                if os.path.exists(self.output_file):
                    print(f"\n📄 Last 10 lines from {self.output_file}:")
                    try:
                        with open(self.output_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in lines[-10:]:
                                print(line.rstrip())
                    except Exception as e:
                        print(f"❌ Error reading file: {e}")
                else:
                    print(f"❌ Output file {self.output_file} not found")
            else:
                print("Unknown command. Use 's', 'o', 't', or 'q'")

def main():
    print("Streaming Voice-to-Text Client")
    print("Continuous recording and transcription")
    
    server_url = input("Server URL (default: http://192.168.0.105:8000): ").strip()
    if not server_url:
        server_url = "http://192.168.0.105:8000"
    
    chunk_duration = input("Chunk duration in seconds (default: 5): ").strip()
    try:
        chunk_duration = int(chunk_duration) if chunk_duration else 5
    except ValueError:
        chunk_duration = 5
    
    output_file = input("Output file (default: live_transcription.txt): ").strip()
    if not output_file:
        output_file = "live_transcription.txt"
    
    client = StreamingVoiceClient(server_url, chunk_duration, output_file)
    client.interactive_mode()
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()