"""
FastAPI Image Text Translation Service
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

from services.text_extractor import TextExtractor
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
    return {"message": "Image Text Translation API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "text_extractor": "ready",
            "translator": "ready",
            "image_processor": "ready",
            "arabic_renderer": "ready"
        }
    }

@app.post("/translate-image")
async def translate_image(file: UploadFile = File(...)):
    """
    Main endpoint to process images:
    1. Extract text using EasyOCR
    2. Translate to Arabic
    3. Apply text masking
    4. Render Arabic text back
    5. Return processed image
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size (200MB limit)
    file_size = 0
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
            
            # Process all images and create ZIP if multiple images
            if len(image_paths) == 1:
                # Single image - return it directly
                processed_image_path = await process_single_image(image_paths[0], temp_dir)
                
                # Read processed image and return as response
                with open(processed_image_path, "rb") as processed_file:
                    processed_content = processed_file.read()
                
                # Determine output filename
                base_name = os.path.splitext(file.filename)[0]
                output_filename = f"{base_name}_translated.png"
                
                return StreamingResponse(
                    BytesIO(processed_content),
                    media_type="image/png",
                    headers={"Content-Disposition": f"attachment; filename={output_filename}"}
                )
            else:
                # Multiple images - process all and return ZIP
                processed_files = []
                for i, image_path in enumerate(image_paths):
                    try:
                        processed_path = await process_single_image(image_path, temp_dir)
                        output_name = f"page_{i+1}_translated.png"
                        processed_files.append((processed_path, output_name))
                    except Exception as e:
                        logger.error(f"Failed to process image {i+1}: {str(e)}")
                        continue
                
                if not processed_files:
                    raise HTTPException(status_code=500, detail="Failed to process any images")
                
                # Create ZIP file
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for processed_path, output_name in processed_files:
                        zip_file.write(processed_path, output_name)
                
                zip_buffer.seek(0)
                base_name = os.path.splitext(file.filename)[0]
                
                return StreamingResponse(
                    BytesIO(zip_buffer.read()),
                    media_type="application/zip",
                    headers={"Content-Disposition": f"attachment; filename={base_name}_translated.zip"}
                )
            
        except Exception as e:
            logger.error(f"Error processing image {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

async def extract_images_from_file(file_path: str, filename: str, temp_dir: str) -> List[str]:
    """
    Extract images from different file types (single image, PDF, or archive)
    
    Args:
        file_path: Path to the input file
        filename: Original filename
        temp_dir: Temporary directory for processing
        
    Returns:
        List of image paths to process
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

async def process_single_image(image_path: str, temp_dir: str) -> str:
    """
    Process a single image through the complete pipeline
    """
    try:
        # 1. Extract text with bounding boxes using EasyOCR
        logger.info("Extracting text from image...")
        text_results = await text_extractor.extract_text_with_boxes(image_path)
        
        if not text_results:
            logger.warning("No text found in image")
            # Return original image if no text found
            output_path = os.path.join(temp_dir, "output.png")
            image_processor.copy_image(image_path, output_path)
            return output_path
        
        # 2. Translate extracted texts to Arabic
        logger.info(f"Translating {len(text_results)} text segments...")
        translated_results = []
        for text_result in text_results:
            original_text = text_result['text']
            translated_text = await translator.translate_to_arabic(original_text)
            translated_results.append({
                'original_text': original_text,
                'translated_text': translated_text,
                'bbox': text_result['bbox'],
                'confidence': text_result['confidence']
            })
        
        # 3. Apply text masking/inpainting
        logger.info("Applying text masking...")
        masked_image_path = await image_processor.mask_text_regions(
            image_path, text_results, temp_dir
        )
        
        # 4. Render Arabic text back onto the image
        logger.info("Rendering Arabic text...")
        final_image_path = await arabic_renderer.render_arabic_text(
            masked_image_path, translated_results, temp_dir
        )
        
        return final_image_path
        
    except Exception as e:
        logger.error(f"Error in process_single_image: {str(e)}")
        raise

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
    
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            processed_files = []
            
            # Process each image
            for i, file in enumerate(files):
                if not file.filename:
                    continue
                    
                # Validate file
                content = await file.read()
                if len(content) > Config.MAX_FILE_SIZE:
                    logger.warning(f"Skipping {file.filename}: file too large")
                    continue
                
                if not file_handler.is_valid_file(file.filename):
                    logger.warning(f"Skipping {file.filename}: invalid file type")
                    continue
                
                # Save and process image
                temp_input_path = os.path.join(temp_dir, f"input_{i}_{file.filename}")
                with open(temp_input_path, "wb") as temp_file:
                    temp_file.write(content)
                
                try:
                    processed_path = await process_single_image(temp_input_path, temp_dir)
                    base_name = os.path.splitext(file.filename)[0]
                    output_name = f"{base_name}_translated.png"
                    processed_files.append((processed_path, output_name))
                except Exception as e:
                    logger.error(f"Failed to process {file.filename}: {str(e)}")
                    continue
            
            if not processed_files:
                raise HTTPException(status_code=400, detail="No images could be processed")
            
            # Create ZIP file
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for processed_path, output_name in processed_files:
                    zip_file.write(processed_path, output_name)
            
            zip_buffer.seek(0)
            
            return StreamingResponse(
                BytesIO(zip_buffer.read()),
                media_type="application/zip",
                headers={"Content-Disposition": "attachment; filename=translated_images.zip"}
            )
            
        except Exception as e:
            logger.error(f"Error processing multiple images: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing images: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
