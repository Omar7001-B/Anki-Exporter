from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, qconnect, tooltip
from aqt.operations import QueryOp
from anki.collection import Collection
from anki.exporting import AnkiPackageExporter
import os
from datetime import datetime
from typing import Dict, Any

def log_deck_hierarchy(col: Collection, export_path: str) -> str:
    """Create a visual tree of the deck hierarchy and save it to a file."""
    try:
        decks = col.decks.all_names_and_ids()
        
        # Create a tree structure
        deck_tree = {}
        
        # Build the tree structure
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
        
        # Create the log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(export_path, f"deck_hierarchy_{timestamp}.txt")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("Anki Deck Hierarchy Tree\n")
            f.write("=======================\n\n")
            f.write(f"Total Decks: {len(decks)}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("Tree View:\n")
            f.write("---------\n\n")
            
            # Print the tree recursively
            def print_tree(node, level=0, is_last=False):
                indent = "│   " * (level - 1) if level > 0 else ""
                if level > 0:
                    indent += "└── " if is_last else "├── "
                
                # Get the deck ID if this is a leaf node
                deck_id = node.get("id")
                id_str = f" (ID: {deck_id})" if deck_id else ""
                
                f.write(f"{indent}{node['name']}{id_str}\n")
                
                # Sort children by name
                children = sorted(node["children"].items(), key=lambda x: x[0])
                
                # Print children
                for i, (_, child) in enumerate(children):
                    is_last_child = i == len(children) - 1
                    print_tree(child, level + 1, is_last_child)
            
            # Print all root decks
            root_decks = sorted(deck_tree.items(), key=lambda x: x[0])
            for i, (_, root_deck) in enumerate(root_decks):
                is_last = i == len(root_decks) - 1
                print_tree(root_deck, 0, is_last)
        
        return log_file
    except Exception as e:
        print(f"Error creating deck hierarchy: {str(e)}")
        return None

def create_folder_structure(export_path: str, deck_name: str) -> str:
    """Create folder structure for a deck and return its export path."""
    parts = deck_name.split("::")
    current_path = export_path
    
    # Create path for this deck level
    for part in parts:
        folder = "".join(x for x in part if x.isalnum() or x in (' ', '-', '_')).strip()
        if folder:
            current_path = os.path.join(current_path, folder)
            if not os.path.exists(current_path):
                os.makedirs(current_path)
    
    return current_path

def export_deck(col: Collection, deck_name: str, export_path: str) -> bool:
    """Export a single deck to the specified path."""
    try:
        deck = col.decks.by_name(deck_name)
        if not deck:
            return False
            
        # Get just the last part of the deck name for the file
        deck_filename = deck_name.split("::")[-1]
        safe_name = "".join(x for x in deck_filename if x.isalnum() or x in (' ', '-', '_')).strip()
        if not safe_name:
            safe_name = "unnamed_deck"
            
        # Create the export filename in the deck's folder
        export_filename = os.path.join(export_path, f"{safe_name}.apkg")
        counter = 1
        while os.path.exists(export_filename):
            export_filename = os.path.join(export_path, f"{safe_name}_{counter}.apkg")
            counter += 1
            
        # Create and configure the exporter
        exporter = AnkiPackageExporter(col)
        exporter.did = deck['id']
        exporter.includeSched = True
        exporter.includeMedia = True
        
        # Export the deck
        exporter.exportInto(export_filename)
        return True
    except Exception as e:
        print(f"Error exporting {deck_name}: {str(e)}")
        return False

def export_all_decks() -> None:
    """Export all decks to user-selected directory with folder structure."""
    # Select export directory
    export_path = QFileDialog.getExistingDirectory(mw, "Select Export Directory")
    if not export_path:
        return
        
    def do_export(col: Collection) -> Dict[str, Any]:
        # Get all decks
        decks = [d.name for d in col.decks.all_names_and_ids()]
        if not decks:
            return {"success": 0, "failed": 0, "total": 0}
            
        success = 0
        failed = 0
        results = []
        
        # Sort decks to ensure parents are created before children
        decks.sort(key=lambda x: len(x.split("::")))
        
        # Process each deck one by one
        for deck_name in decks:
            try:
                # Create the appropriate folder structure
                deck_path = create_folder_structure(export_path, deck_name)
                
                # Export the deck to that folder
                if export_deck(col, deck_name, deck_path):
                    success += 1
                    results.append({
                        "deck_name": deck_name,
                        "success": True,
                        "export_path": deck_path
                    })
                else:
                    failed += 1
                    results.append({
                        "deck_name": deck_name,
                        "success": False,
                        "error": "Export failed"
                    })
            except Exception as e:
                failed += 1
                results.append({
                    "deck_name": deck_name,
                    "success": False,
                    "error": str(e)
                })
        
        # Create log file
        log_file = None
        try:
            log_file = log_deck_hierarchy(col, export_path)
        except Exception as e:
            print(f"Error creating deck hierarchy: {str(e)}")
        
        return {
            "success": success, 
            "failed": failed, 
            "total": len(decks),
            "results": results,
            "log_file": log_file
        }
    
    def on_success(result: Dict[str, Any]) -> None:
        log_file = result.get("log_file")
        success = result.get("success", 0)
        failed = result.get("failed", 0)
        total = result.get("total", 0)
        
        message = f"Export complete!\n\n"
        message += f"Successfully exported: {success} of {total} decks\n"
        message += f"Failed: {failed} decks\n"
        
        if log_file:
            message += f"\nDeck hierarchy saved to:\n{os.path.basename(log_file)}"
            
            # Open the log file if it exists
            if os.path.exists(log_file):
                try:
                    if os.name == 'nt':  # Windows
                        os.startfile(log_file)
                    else:  # macOS or Linux
                        import subprocess
                        subprocess.call(['open', log_file] if os.name == 'posix' else ['xdg-open', log_file])
                except Exception as e:
                    print(f"Error opening log file: {str(e)}")
        
        showInfo(message)
    
    # Show "Working" tooltip before starting
    tooltip("Starting export...", period=1000)
    
    # Run export in background
    QueryOp(
        parent=mw,
        op=lambda col: do_export(col),
        success=on_success
    ).run_in_background()

# Add menu item
action_export = QAction("Export All Decks", mw)
qconnect(action_export.triggered, export_all_decks)
mw.form.menuTools.addAction(action_export) 