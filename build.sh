#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Create a directory for NLTK data
mkdir -p nltk_data

# Set NLTK data path
export NLTK_DATA=$(pwd)/nltk_data

# Download 'punkt'
python -m nltk.downloader all
