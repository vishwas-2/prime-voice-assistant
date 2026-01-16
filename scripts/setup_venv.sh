#!/bin/bash
# Setup script for PRIME Voice Assistant virtual environment (Unix/macOS)

set -e

echo "=========================================="
echo "PRIME Voice Assistant - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install PRIME in development mode
echo ""
echo "Installing PRIME in development mode..."
pip install -e .

# Download spaCy model
echo ""
echo "Downloading spaCy language model..."
python -m spacy download en_core_web_sm

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start PRIME, run:"
echo "  prime"
echo ""
