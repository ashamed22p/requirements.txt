# Image Text Translation API

## Overview

This is a FastAPI-based service that extracts text from images, translates it to Arabic, and re-renders the translated text back onto the images. The application supports multiple input formats including single images, PDF files, and compressed archives (ZIP, RAR, CBZ, CBR). It uses EasyOCR for text extraction, OpenCV for text masking/inpainting, and deep-translator for translation services.

**Current Status**: Basic API structure is running on port 5000 with core packages installed. Full OCR and translation features are implemented but require additional ML packages (EasyOCR, OpenCV, etc.) that are being installed incrementally due to disk space constraints.

## User Preferences

Preferred communication style: Simple, everyday language.
User requested comprehensive project with all features from the attached Arabic requirements.

## Recent Changes

- **2025-01-21**: Added path resolution imports to main.py and main_enhanced.py per user request
- **2025-01-21**: Fixed duplicate import statements in both main files
- **2025-01-21**: Resolved disk space issues by cleaning up unused PyTorch packages
- **2025-01-20**: Created complete project architecture with all required services
- **2025-01-20**: Updated file size limit to 200MB as requested  
- **2025-01-20**: Added support for PDF and archive file processing
- **2025-01-20**: Basic API is running successfully on port 5000 with CORS enabled
- **2025-01-20**: Core packages installed (FastAPI, uvicorn, PIL, numpy, deep-translator, arabic-reshaper, python-bidi)
- **2025-01-20**: Prepared for Render deployment with PORT environment variable support
- **2025-01-20**: Created render_requirements.txt, start.sh, and render.yaml for deployment
- **2025-01-20**: User confirmed in Arabic that system works completely according to specifications

## System Architecture

The application follows a microservices architecture pattern with clear separation of concerns:

- **API Layer**: FastAPI handles HTTP requests and responses
- **Service Layer**: Modular services for text extraction, translation, image processing, and text rendering
- **Utility Layer**: File handling and validation utilities
- **Configuration Layer**: Centralized configuration management

### Key Architectural Decisions

1. **Asynchronous Processing**: Uses async/await pattern with thread pools for CPU-intensive operations to prevent blocking the main event loop
2. **Memory Management**: Implements streaming file processing and temporary file management to handle large files (up to 200MB) without excessive memory usage
3. **Modular Design**: Each service has a single responsibility, making the system maintainable and testable

## Key Components

### Services

1. **TextExtractor** (`services/text_extractor.py`)
   - Uses EasyOCR for multi-language text detection
   - Extracts text with bounding box coordinates
   - Filters results based on confidence threshold (0.3)

2. **TextTranslator** (`services/translator.py`)
   - Uses deep-translator (Google Translate) for translation
   - Auto-detects source language and translates to Arabic
   - Includes text cleaning and Arabic language detection

3. **ImageProcessor** (`services/image_processor.py`)
   - Handles text masking using OpenCV inpainting
   - Removes original text while preserving background quality
   - Uses professional inpainting techniques

4. **ArabicTextRenderer** (`services/arabic_text_renderer.py`)
   - Renders Arabic text with proper RTL support
   - Uses arabic_reshaper and python-bidi for correct display
   - Calculates appropriate font sizes based on original text bbox

### Utilities

1. **FileHandler** (`utils/file_handler.py`)
   - Validates supported file formats
   - Handles MIME type checking
   - Supports images, PDFs, and archives

### Configuration

1. **Config** (`config.py`)
   - Centralized configuration management
   - File size limits (50MB max)
   - Processing parameters and thresholds
   - API and CORS settings

## Data Flow

1. **File Upload**: Client uploads image/PDF/archive via POST endpoint
2. **File Validation**: FileHandler validates format and size
3. **Archive Extraction**: If needed, extracts images from archives or converts PDF pages
4. **Text Extraction**: EasyOCR extracts text with bounding boxes from each image
5. **Text Translation**: Deep-translator translates extracted text to Arabic
6. **Image Processing**: OpenCV removes original text using inpainting
7. **Text Rendering**: Arabic text is rendered back onto images with proper formatting
8. **Response**: Processed images are packaged in ZIP file for download
9. **Cleanup**: Temporary files are automatically removed

## External Dependencies

### Core Libraries
- **FastAPI**: Web framework for API development
- **EasyOCR**: Text extraction from images
- **OpenCV**: Image processing and inpainting
- **Pillow (PIL)**: Image manipulation and text rendering
- **deep-translator**: Translation services

### Arabic Text Processing
- **arabic_reshaper**: Arabic text reshaping for proper display
- **python-bidi**: Bidirectional text algorithm for RTL languages

### File Processing
- **pdf2image**: PDF to image conversion
- **zipfile/rarfile**: Archive extraction
- **patool/pyunpack**: Additional archive format support

### Font Requirements
- **Amiri-Regular.ttf**: Arabic font file for text rendering

## Deployment Strategy

The application is designed for containerized deployment with the following considerations:

1. **Resource Management**: Implements memory-efficient processing for large files
2. **Scalability**: Async design allows handling multiple concurrent requests
3. **Error Handling**: Graceful fallbacks for failed operations
4. **CORS Configuration**: Allows cross-origin requests for web integration
5. **Logging**: Comprehensive logging for monitoring and debugging

### Environment Requirements
- Python 3.8+
- Sufficient disk space for temporary file processing
- Font files accessible in the fonts/ directory
- Network access for translation services (Google Translate)

### Performance Optimizations
- Thread pool execution for CPU-intensive tasks
- Streaming file processing to reduce memory usage
- Automatic cleanup of temporary resources
- Configurable processing parameters for quality vs. speed trade-offs