#!/bin/bash
# SD-Host startup script for Linux/macOS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SD-Host: Stable Diffusion RESTful API Service${NC}"
echo "Starting up..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements/requirements.txt
fi

# Create necessary directories
mkdir -p models output data logs

# Check if config file exists
if [ ! -f "config/config.yml" ]; then
    echo -e "${YELLOW}Config file not found. Copying from example...${NC}"
    cp config/config.example.yml config/config.yml
    echo -e "${YELLOW}Please edit config/config.yml before running the service${NC}"
fi

# Start the service
echo -e "${GREEN}Starting SD-Host service...${NC}"
python src/main.py
