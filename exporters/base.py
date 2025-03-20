import os
import json
from typing import Dict, Any, List
from datetime import datetime
from anki.collection import Collection
from ..utils.files import create_folder_structure
from ..utils.deck import log_deck_hierarchy

class BaseExporter:
    """Base class for all exporters with common functionality."""
    
    def __init__(self, collection):
        self.col = collection
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {str(e)}")
            return {}
            
    def prepare_export_path(self, export_path: str, deck_name: str) -> str:
        """Prepare the export path for a deck."""
        # Get folder structure settings
        folder_config = self.config.get('folder_structure', {})
        sanitize = folder_config.get('sanitize', True)
        allowed_chars = folder_config.get('allowed_chars', [' ', '-', '_'])
        max_depth = folder_config.get('max_depth', 10)
        
        # Split deck name into parts
        parts = deck_name.split('::')
        if len(parts) > max_depth:
            parts = parts[:max_depth]
            
        # Create path
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
        
    def create_log_file(self, export_path: str) -> str:
        """Create a log file for deck hierarchy."""
        if not self.config.get('logging', {}).get('create_hierarchy_log', True):
            return None
            
        log_dir = os.path.join(export_path, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f'deck_hierarchy_{timestamp}.txt')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Deck Hierarchy:\n\n")
            for deck in self.col.decks.all_names_and_ids():
                f.write(f"{deck.name}\n")
                
        return log_file
        
    def get_child_decks(self, deck_name: str) -> List[str]:
        """Get all child decks of a given deck."""
        child_decks = []
        for deck in self.col.decks.all_names_and_ids():
            if deck.name.startswith(deck_name + '::'):
                child_decks.append(deck.name)
        return child_decks
        
    def get_parent_deck(self, deck_name: str) -> tuple[str, str]:
        """Get the parent deck name and HTML for navigation."""
        parts = deck_name.split('::')
        if len(parts) > 1:
            parent_name = '::'.join(parts[:-1])
            parent_html = f'<div class="parent-link"><a href="../index.html">← Back to {parent_name}</a></div>'
            return parent_name, parent_html
        return None, '' 