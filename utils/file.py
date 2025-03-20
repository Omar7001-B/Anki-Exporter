import os
import re
from typing import Optional

def sanitize_filename(filename: str, allowed_chars: str = None) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename: The filename to sanitize
        allowed_chars: String of allowed characters (default: alphanumeric, spaces, hyphens, underscores)
        
    Returns:
        Sanitized filename
    """
    if allowed_chars is None:
        allowed_chars = r'[a-zA-Z0-9\s\-_]'
    
    # Replace invalid characters with underscores
    sanitized = re.sub(f'[^{allowed_chars}]', '_', filename)
    
    # Replace multiple underscores with a single one
    sanitized = re.sub('_+', '_', sanitized)
    
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip('_ ')
    
    # If the filename is empty after sanitization, use a default name
    if not sanitized:
        sanitized = 'unnamed'
        
    return sanitized

def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to ensure
        
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False

def get_relative_path(from_path: str, to_path: str) -> str:
    """
    Get the relative path from one path to another.
    
    Args:
        from_path: Starting path
        to_path: Target path
        
    Returns:
        Relative path from from_path to to_path
    """
    try:
        return os.path.relpath(to_path, from_path)
    except ValueError:
        # If paths are on different drives (Windows), return absolute path
        return to_path

def copy_file(src: str, dst: str) -> bool:
    """
    Copy a file from source to destination.
    
    Args:
        src: Source file path
        dst: Destination file path
        
    Returns:
        True if copy was successful, False otherwise
    """
    try:
        # Ensure destination directory exists
        dst_dir = os.path.dirname(dst)
        if not ensure_directory(dst_dir):
            return False
            
        # Copy the file
        import shutil
        shutil.copy2(src, dst)
        return True
    except Exception as e:
        print(f"Error copying file from {src} to {dst}: {e}")
        return False

def get_file_size(file_path: str) -> Optional[int]:
    """
    Get the size of a file in bytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in bytes, or None if file doesn't exist or can't be accessed
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return None 