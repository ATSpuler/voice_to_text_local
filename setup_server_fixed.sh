#!/bin/bash
# SAFE Setup script - run from project directory

echo "🚀 Setting up Voice-to-Text Server..."

# Check we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project directory (where pyproject.toml exists)"
    echo "Current directory: $(pwd)"
    echo "Expected files: pyproject.toml, server.py, client.py"
    exit 1
fi

# Check existing NVIDIA setup
echo "Checking existing NVIDIA setup..."
nvidia-smi
if [ $? -ne 0 ]; then
    echo "❌ NVIDIA driver issue - stopping for safety"
    exit 1
fi
echo "✅ NVIDIA driver working - proceeding safely"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies from pyproject.toml
pip install --upgrade pip

# Install PyTorch with CUDA support first (for RTX 3060)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install fastapi uvicorn python-multipart requests websockets
pip install openai-whisper

# Test PyTorch CUDA
echo "Testing PyTorch CUDA integration..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
    print('✅ GPU setup successful!')
else:
    print('⚠️  CUDA not available - check installation')
"

echo ""
echo "✅ Setup complete!"
echo "To start server:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate" 
echo "  python server.py"