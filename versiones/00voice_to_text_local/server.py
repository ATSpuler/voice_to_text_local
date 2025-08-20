#!/usr/bin/env python3
"""
Voice-to-Text Server
Runs on Ubuntu GPU server, handles audio transcription using Whisper
"""

import os
import tempfile
import whisper
import torch
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

app = FastAPI(title="Voice-to-Text Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model: Optional[whisper.Whisper] = None

def load_whisper_model(model_size: str = "base"):
    """Load Whisper model on GPU if available"""
    global model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading Whisper {model_size} model on {device}...")
    
    model = whisper.load_model(model_size, device=device)
    print(f"Model loaded successfully on {device}")
    return model

@app.on_event("startup")
async def startup_event():
    """Initialize model on server startup"""
    # Use 'base' model for 12GB GPU - can upgrade to 'large' if needed
    load_whisper_model("large")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model_loaded": model is not None,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu_available": torch.cuda.is_available()
    }

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transcribe uploaded audio file"""
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")
    
    if not audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be audio format")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Transcribe with Whisper
        result = model.transcribe(tmp_file_path)
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        }
    
    except Exception as e:
        # Clean up temp file on error
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/model-info")
async def model_info():
    """Get current model information"""
    if model is None:
        return {"model_loaded": False}
    
    return {
        "model_loaded": True,
        "device": str(model.device),
        "model_size": getattr(model, 'model_size', 'unknown')
    }

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )