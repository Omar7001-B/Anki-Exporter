import os
from typing import Optional, Tuple
from PIL import Image
import io

def process_image(image_data: bytes, max_size: Optional[int] = None, quality: int = 85) -> Optional[bytes]:
    """
    Process an image by resizing and compressing it if necessary.
    
    Args:
        image_data: Raw image data
        max_size: Maximum dimension (width or height) in pixels
        quality: JPEG quality (1-100)
        
    Returns:
        Processed image data as bytes, or None if processing failed
    """
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if necessary
        if max_size:
            ratio = max_size / max(img.size)
            if ratio < 1:
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save as JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def get_image_dimensions(image_data: bytes) -> Optional[Tuple[int, int]]:
    """
    Get the dimensions of an image.
    
    Args:
        image_data: Raw image data
        
    Returns:
        Tuple of (width, height) in pixels, or None if dimensions couldn't be determined
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception:
        return None

def is_valid_image(image_data: bytes) -> bool:
    """
    Check if the given data is a valid image.
    
    Args:
        image_data: Raw image data
        
    Returns:
        True if the data is a valid image, False otherwise
    """
    try:
        img = Image.open(io.BytesIO(image_data))
        img.verify()
        return True
    except Exception:
        return False

def get_media_type(file_path: str) -> Optional[str]:
    """
    Determine the media type of a file based on its extension.
    
    Args:
        file_path: Path to the media file
        
    Returns:
        Media type (e.g., 'image', 'audio', 'video'), or None if unknown
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # Image extensions
    if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'):
        return 'image'
    
    # Audio extensions
    if ext in ('.mp3', '.wav', '.ogg', '.m4a'):
        return 'audio'
    
    # Video extensions
    if ext in ('.mp4', '.webm', '.mov'):
        return 'video'
    
    return None 