import os
import shutil
import re
from typing import List

def create_folder_structure(
    export_path: str, 
    deck_name: str,
    sanitize: bool = True,
    allowed_chars: List[str] = None,
    max_depth: int = 10
) -> str:
    """Create folder structure for a deck and return its export path."""
    if allowed_chars is None:
        allowed_chars = [' ', '-', '_']
        
    parts = deck_name.split("::")
    if len(parts) > max_depth:
        parts = parts[:max_depth]
        
    current_path = export_path
    
    for part in parts:
        if sanitize:
            folder = "".join(x for x in part if x.isalnum() or x in allowed_chars).strip()
        else:
            folder = part.strip()
            
        if folder:
            current_path = os.path.join(current_path, folder)
            if not os.path.exists(current_path):
                os.makedirs(current_path)
    
    return current_path

def process_media_files(
    content: str, 
    media_dir: str, 
    collection_media_path: str,
    max_image_size: int = 1920,
    image_quality: int = 85
) -> str:
    """Process media files in content and copy them to media directory."""
    for match in re.findall(r'<img src="([^"]+)"', content):
        if os.path.exists(os.path.join(collection_media_path, match)):
            src_path = os.path.join(collection_media_path, match)
            dst_path = os.path.join(media_dir, match)
            
            # Create necessary subdirectories
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # Copy and optionally process the image
            if match.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    from PIL import Image
                    with Image.open(src_path) as img:
                        # Resize if needed
                        if max(img.size) > max_image_size:
                            ratio = max_image_size / max(img.size)
                            new_size = tuple(int(dim * ratio) for dim in img.size)
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                        
                        # Save with specified quality
                        img.save(dst_path, quality=image_quality)
                except Exception as e:
                    print(f"Error processing image {match}: {str(e)}")
                    shutil.copy2(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
            
            # Update path to use relative media directory
            content = content.replace(f'<img src="{match}"', f'<img src="media/{match}"')
    return content

def ensure_media_directory(export_path: str, media_folder: str = "media") -> str:
    """Ensure media directory exists and return its path."""
    media_dir = os.path.join(export_path, media_folder)
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    return media_dir 