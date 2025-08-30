#!/usr/bin/env python3
"""
Simple trigger script for voice client
Usage: python trigger.py [toggle|start|stop|status]
"""

import socket
import sys
import os

def send_command(command):
    """Send command to voice client via Unix socket"""
    socket_path = "/tmp/voice_client.sock"
    
    if not os.path.exists(socket_path):
        print("❌ Voice client not running (socket not found)")
        return False
    
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        sock.send(command.encode('utf-8'))
        
        # For status command, read response
        if command == 'status':
            response = sock.recv(1024).decode('utf-8')
            print(f"Status: {response}")
        else:
            print(f"✅ Sent: {command}")
        
        sock.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to send command: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python trigger.py [toggle|start|stop|status]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command not in ['toggle', 'start', 'stop', 'status']:
        print("❌ Invalid command. Use: toggle, start, stop, or status")
        sys.exit(1)
    
    send_command(command)

if __name__ == "__main__":
    main()