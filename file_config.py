"""
Configuration file for supported file types in the RAG system.
File types are organized by categories for more flexible processing.
"""

# Text-based document file types
TEXT_DOCUMENT_TYPES = [
    "pdf",      # PDF documents
    "docx",     # Microsoft Word
    "txt",      # Plain text
    "md",       # Markdown
    "html",     # HTML documents
    "rtf",      # Rich Text Format
    "odt",      # OpenDocument Text
]

# Spreadsheet file types
SPREADSHEET_TYPES = [
    "xlsx",     # Microsoft Excel
    "csv",      # Comma-separated values
    "ods",      # OpenDocument Spreadsheet
    "tsv",      # Tab-separated values
]

# Presentation file types
PRESENTATION_TYPES = [
    "pptx",     # Microsoft PowerPoint
    "odp",      # OpenDocument Presentation
]

# Image file types (if OCR is supported)
IMAGE_TYPES = [
    "png",
    "jpg",
    "jpeg",
    "tiff",
    "bmp",
]

# Audio file types (if speech-to-text is supported)
AUDIO_TYPES = [
    "mp3",
    "wav",
    "ogg",
    "flac",
    "m4a",
]

# Video file types (if video transcription is supported)
VIDEO_TYPES = [
    "mp4",
    "avi",
    "mov",
    "mkv",
    "webm",
]

# Default categories to process (can be modified at runtime)
DEFAULT_ENABLED_CATEGORIES = [
    "text_documents",
    "spreadsheets",
    "presentations",
]

# Category mapping for easier reference
CATEGORY_MAP = {
    "text_documents": TEXT_DOCUMENT_TYPES,
    "spreadsheets": SPREADSHEET_TYPES,
    "presentations": PRESENTATION_TYPES,
    "images": IMAGE_TYPES,
    "audio": AUDIO_TYPES,
    "video": VIDEO_TYPES,
}

def get_enabled_file_types(categories=None):
    """
    Get a list of file extensions for enabled categories.
    
    Args:
        categories: List of category names to enable. If None, uses DEFAULT_ENABLED_CATEGORIES.
        
    Returns:
        List of file extensions (without dots) for all enabled categories.
    """
    if categories is None:
        categories = DEFAULT_ENABLED_CATEGORIES
        
    enabled_types = []
    for category in categories:
        if category in CATEGORY_MAP:
            enabled_types.extend(CATEGORY_MAP[category])
            
    return enabled_types

def get_all_categories():
    """
    Get a list of all available category names.
    
    Returns:
        List of category names.
    """
    return list(CATEGORY_MAP.keys())

def get_category_for_extension(extension):
    """
    Find the category for a given file extension.
    
    Args:
        extension: File extension (without dot)
        
    Returns:
        Category name or None if not found
    """
    extension = extension.lower().lstrip('.')
    
    for category, extensions in CATEGORY_MAP.items():
        if extension in extensions:
            return category
            
    return None 