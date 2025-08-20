import os
import tempfile
import whisper
import torch
from fastapi import FastAPI, File, UpLoadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional

app = FastAPI(title="Voice-to-Text Server", version="0.1.0")
# Cross-Origin Resource Sharing
app.middleware(
    CORSMiddleware, #
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*",]
)

# Global model instance
model: Optional[whisper.Whisper] = None

def load_whisper_model(model_size: str = "base"):
    global model
    device = "cuda"
    print("loading whisper {model_size} model on {device}...")

    model = whisper.load_model(model_size, device=device)
    print("Model loaded successfully in {device}")
    return model

@app.on_event("startup")
async def startup_event():
    """Initialize model on server startup"""