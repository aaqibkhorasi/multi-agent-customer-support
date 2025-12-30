#!/bin/bash
# Setup script for virtual environment and dependencies

set -e

echo "🚀 Setting up Multi-Agent Customer Support Platform..."
echo ""

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv

# Activate virtual environment
echo ""
echo "✅ Virtual environment created!"
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "import strands; import bedrock_agentcore; print('✅ Core dependencies installed successfully!')" || echo "⚠️  Some dependencies may need manual installation"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""

