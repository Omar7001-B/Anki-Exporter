from anki.collection import Collection
from datetime import datetime
import os
from typing import Optional

def build_deck_tree(decks: list) -> dict:
    """Build deck hierarchy tree structure."""
    deck_tree = {}
    
    for deck in decks:
        parts = deck.name.split("::")
        current_dict = deck_tree
        
        for i, part in enumerate(parts):
            full_path = "::".join(parts[:i+1])
            if full_path not in current_dict:
                current_dict[full_path] = {
                    "name": part,
                    "id": deck.id if i == len(parts)-1 else None,
                    "children": {}
                }
            current_dict = current_dict[full_path]["children"]
    
    return deck_tree

def log_deck_hierarchy(collection, export_path: str) -> Optional[str]:
    """
    Create a log file with the deck hierarchy.
    
    Args:
        collection: Anki collection
        export_path: Base export directory
        
    Returns:
        Path to the log file or None if it couldn't be created
    """
    try:
        # Create logs directory
        logs_dir = os.path.join(export_path, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f'deck_hierarchy_{timestamp}.txt')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Deck Hierarchy Export\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            # Get all decks and sort by name
            decks = sorted(collection.decks.all_names_and_ids(), key=lambda x: x.name)
            
            # Display them with indentation based on hierarchy
            for deck in decks:
                # Count the number of '::' to determine depth
                depth = deck.name.count('::')
                indent = '  ' * depth
                
                # Get the last part of the name (after last '::')
                if '::' in deck.name:
                    display_name = deck.name.split('::')[-1]
                else:
                    display_name = deck.name
                    
                f.write(f"{indent}• {display_name} ({deck.name})\n")
                
        return log_file
    except Exception as e:
        print(f"Error creating deck hierarchy log: {str(e)}")
        return None
        
def get_child_decks(collection, deck_name: str, direct_only: bool = True) -> list:
    """
    Get child decks for a given deck.
    
    Args:
        collection: Anki collection
        deck_name: Name of the parent deck
        direct_only: If True, only return direct children
        
    Returns:
        List of child deck names
    """
    child_decks = []
    
    if direct_only:
        # Count parts in parent name
        parent_parts = deck_name.split('::')
        parent_parts_count = len(parent_parts)
        
        # Find decks that have exactly one more part
        for deck in collection.decks.all_names_and_ids():
            if deck.name.startswith(deck_name + '::'):
                child_parts = deck.name.split('::')
                if len(child_parts) == parent_parts_count + 1:
                    child_decks.append(deck.name)
    else:
        # Get all descendants
        for deck in collection.decks.all_names_and_ids():
            if deck.name.startswith(deck_name + '::'):
                child_decks.append(deck.name)
                
    return sorted(child_decks) 