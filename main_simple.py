"""
FastAPI Image Text Translation Service - Simplified Version
Extracts text from images, translates to Arabic, and re-renders on images
"""

import os
import tempfile
import zipfile
from io import BytesIO
from typing import List, Optional
import asyncio
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn

from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Image Text Translation API",
    description="Extract text from images, translate to Arabic, and re-render",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Image Text Translation API is running",
        "status": "healthy",
        "supported_formats": ["PNG", "JPG", "JPEG", "WebP", "BMP", "TIFF", "GIF", "PDF", "ZIP", "RAR", "CBZ", "CBR"],
        "max_file_size_mb": Config.MAX_FILE_SIZE // (1024 * 1024)
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "ready",
            "file_handler": "ready",
            "cors": "enabled"
        },
        "config": {
            "max_file_size_mb": Config.MAX_FILE_SIZE // (1024 * 1024),
            "max_batch_size": Config.MAX_BATCH_SIZE
        }
    }

@app.post("/translate-image")
async def translate_image(file: UploadFile = File(...)):
    """
    Main endpoint to process images:
    1. Extract text using OCR
    2. Translate to Arabic
    3. Apply text masking
    4. Render Arabic text back
    5. Return processed image
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size (200MB limit)
    content = await file.read()
    file_size = len(content)
    
    if file_size > Config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {Config.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # For now, return a simple response indicating the service is ready
    # The full implementation with OCR and translation will be added once all dependencies are available
    return {
        "message": "File received successfully",
        "filename": file.filename,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "status": "Service is ready - full OCR and translation features will be available once all dependencies are installed"
    }

@app.post("/translate-multiple")
async def translate_multiple_images(files: List[UploadFile] = File(...)):
    """
    Process multiple images and return them as a ZIP file
    """
    if len(files) > Config.MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Too many files. Maximum batch size is {Config.MAX_BATCH_SIZE}"
        )
    
    # For now, return a simple response
    return {
        "message": f"Received {len(files)} files",
        "files": [f.filename for f in files if f.filename],
        "status": "Service is ready - full batch processing will be available once all dependencies are installed"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )