#!/bin/bash
# SAFE Setup script for Ubuntu GPU Server
# Does NOT touch existing NVIDIA drivers

echo "🚀 Setting up Voice-to-Text Server (preserving existing drivers)..."

# Check existing NVIDIA setup first
echo "Checking existing NVIDIA setup..."
nvidia-smi
if [ $? -eq 0 ]; then
    echo "✅ NVIDIA driver already working - will NOT modify"
else
    echo "❌ NVIDIA driver issue detected - stopping for safety"
    exit 1
fi

# Update package list only
sudo apt update

# Install Python and development tools (safe)
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install audio processing libraries (safe)
sudo apt install -y ffmpeg portaudio19-dev

# Create isolated virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies in virtual environment
pip install --upgrade pip
pip install -e .

# Test PyTorch CUDA availability
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
else:
    print('⚠️  CUDA not available to PyTorch - may need different PyTorch version')
"

echo ""
echo "✅ Safe setup complete - existing drivers preserved!"
echo "To start server: source venv/bin/activate && python server.py"