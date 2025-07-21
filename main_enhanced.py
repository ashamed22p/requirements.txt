"""
FastAPI Image Text Translation Service - Enhanced Version
Extracts text from images, translates to Arabic, and re-renders on images
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

try:
    from services.text_extractor import TextExtractor
    OCR_AVAILABLE = True
except ImportError:
    from services.text_extractor_fallback import TextExtractorFallback as TextExtractor
    OCR_AVAILABLE = False

from services.translator import TextTranslator
from services.image_processor import ImageProcessor
from services.arabic_text_renderer import ArabicTextRenderer
from utils.file_handler import FileHandler
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

# Initialize services
text_extractor = TextExtractor()
translator = TextTranslator()
image_processor = ImageProcessor()
arabic_renderer = ArabicTextRenderer()
file_handler = FileHandler()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Image Text Translation API is running",
        "status": "healthy",
        "supported_formats": ["PNG", "JPG", "JPEG", "WebP", "BMP", "TIFF", "GIF", "PDF", "ZIP", "RAR", "CBZ", "CBR"],
        "max_file_size_mb": Config.MAX_FILE_SIZE // (1024 * 1024),
        "features": {
            "translation": "available",
            "image_processing": "available", 
            "arabic_rendering": "available",
            "pdf_extraction": "available",
            "archive_extraction": "available",
            "ocr": "available" if OCR_AVAILABLE else "pending_installation"
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "translator": "ready",
            "image_processor": "ready",
            "arabic_renderer": "ready",
            "file_handler": "ready"
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
    1. Extract text using OCR (when available)
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
    
    # Validate file type
    if not file_handler.is_valid_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Supported formats: PNG, JPG, JPEG, WebP, BMP, TIFF, GIF, PDF, ZIP, RAR, CBZ, CBR"
        )
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Save uploaded file temporarily
            temp_input_path = os.path.join(temp_dir, f"input_{file.filename}")
            with open(temp_input_path, "wb") as temp_file:
                temp_file.write(content)
            
            logger.info(f"Processing file: {file.filename}")
            
            # Extract images from the file based on its type
            image_paths = await extract_images_from_file(temp_input_path, file.filename, temp_dir)
            
            if not image_paths:
                raise HTTPException(status_code=400, detail="No images found in the file")
            
            # For now, return information about what would be processed
            # Once OCR is available, full processing will be implemented
            result = {
                "message": "File processed successfully",
                "filename": file.filename,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "extracted_images": len(image_paths),
                "status": "Ready for processing - OCR integration pending",
                "next_steps": [
                    "Install EasyOCR for text extraction",
                    "Process each extracted image",
                    "Translate detected text to Arabic", 
                    "Apply text masking and re-render"
                ]
            }
            
            if len(image_paths) == 1:
                result["processing_mode"] = "single_image"
            else:
                result["processing_mode"] = "batch_processing"
                result["output_format"] = "zip_file"
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

async def extract_images_from_file(file_path: str, filename: str, temp_dir: str) -> List[str]:
    """
    Extract images from different file types (single image, PDF, or archive)
    """
    try:
        if file_handler.is_image_file(filename):
            # Single image file
            return [file_path]
        elif file_handler.is_pdf_file(filename):
            # PDF file - extract pages as images
            return file_handler.extract_images_from_pdf(file_path, temp_dir)
        elif file_handler.is_archive_file(filename):
            # Archive file - extract contained images
            return file_handler.extract_images_from_archive(file_path, temp_dir)
        else:
            logger.error(f"Unsupported file type: {filename}")
            return []
            
    except Exception as e:
        logger.error(f"Error extracting images from {filename}: {str(e)}")
        return []

@app.post("/translate-text")
async def translate_text_endpoint(request: dict):
    """
    Direct text translation endpoint for testing
    """
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text field is required")
        
        translated = await translator.translate_to_arabic(text)
        return {
            "original_text": text,
            "translated_text": translated,
            "language": "Arabic"
        }
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/extract-archive")
async def extract_archive_endpoint(file: UploadFile = File(...)):
    """
    Test endpoint for archive extraction
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file_handler.is_archive_file(file.filename):
        raise HTTPException(status_code=400, detail="File is not an archive")
    
    content = await file.read()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        try:
            extracted_images = file_handler.extract_images_from_archive(temp_file_path, temp_dir)
            return {
                "archive_name": file.filename,
                "extracted_images": len(extracted_images),
                "image_files": [os.path.basename(path) for path in extracted_images]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@app.post("/extract-pdf")
async def extract_pdf_endpoint(file: UploadFile = File(...)):
    """
    Test endpoint for PDF extraction
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    if not file_handler.is_pdf_file(file.filename):
        raise HTTPException(status_code=400, detail="File is not a PDF")
    
    content = await file.read()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, file.filename)
        with open(temp_file_path, "wb") as f:
            f.write(content)
        
        try:
            extracted_images = file_handler.extract_images_from_pdf(temp_file_path, temp_dir)
            return {
                "pdf_name": file.filename,
                "extracted_pages": len(extracted_images),
                "page_files": [os.path.basename(path) for path in extracted_images]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )