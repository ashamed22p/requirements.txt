#!/bin/bash
# Start script for Render deployment

# Install dependencies
pip install -r render_requirements.txt

# Run the FastAPI application
python main_enhanced.py