"""
Configuration settings for the Image Text Translation API
"""

import os
from typing import Dict, Any

class Config:
    """Application configuration"""
    
    # File size limits
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB in bytes
    MAX_BATCH_SIZE = 10  # Maximum number of files in batch processing
    
    # Image processing settings
    MAX_IMAGE_DIMENSION = 2048  # Maximum width/height for processing
    OCR_CONFIDENCE_THRESHOLD = 0.3  # Minimum confidence for text detection
    
    # Text processing settings
    MIN_TEXT_LENGTH = 2  # Minimum text length to process
    BBOX_EXPANSION_RATIO = 0.15  # Expansion ratio for text bounding boxes
    
    # Font settings
    FONT_PATH = "fonts/Amiri-Regular.ttf"
    FALLBACK_FONT_SIZE = 20
    MIN_FONT_SIZE = 8
    MAX_FONT_SIZE = 100
    
    # Temporary file settings
    TEMP_DIR_PREFIX = "img_translate_"
    AUTO_CLEANUP = True
    
    # API settings
    API_TITLE = "Image Text Translation API"
    API_DESCRIPTION = "Extract text from images, translate to Arabic, and re-render"
    API_VERSION = "1.0.0"
    
    # CORS settings
    CORS_ORIGINS = ["*"]
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    # Logging settings
    LOG_LEVEL = "INFO"
    
    # Translation settings
    TRANSLATION_TARGET_LANG = "ar"  # Arabic
    TRANSLATION_SOURCE_LANG = "auto"  # Auto-detect
    
    # OCR settings
    OCR_LANGUAGES = ['en', 'ar', 'fr', 'es', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh']
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as dictionary"""
        return {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and not callable(getattr(cls, attr))
        }
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        try:
            # Check required directories
            os.makedirs("fonts", exist_ok=True)
            
            # Validate file size limits
            assert cls.MAX_FILE_SIZE > 0, "MAX_FILE_SIZE must be positive"
            assert cls.MAX_BATCH_SIZE > 0, "MAX_BATCH_SIZE must be positive"
            
            # Validate image settings
            assert cls.MAX_IMAGE_DIMENSION > 0, "MAX_IMAGE_DIMENSION must be positive"
            assert 0 <= cls.OCR_CONFIDENCE_THRESHOLD <= 1, "OCR_CONFIDENCE_THRESHOLD must be between 0 and 1"
            
            # Validate font settings
            assert cls.MIN_FONT_SIZE > 0, "MIN_FONT_SIZE must be positive"
            assert cls.MAX_FONT_SIZE > cls.MIN_FONT_SIZE, "MAX_FONT_SIZE must be greater than MIN_FONT_SIZE"
            
            return True
            
        except AssertionError as e:
            print(f"Configuration validation failed: {e}")
            return False
        except Exception as e:
            print(f"Configuration validation error: {e}")
            return False

# Environment-based overrides
if os.getenv("DEBUG"):
    Config.LOG_LEVEL = "DEBUG"

if os.getenv("MAX_FILE_SIZE"):
    try:
        Config.MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))
    except ValueError:
        pass

# Validate configuration on import
if not Config.validate_config():
    raise RuntimeError("Invalid configuration settings")
