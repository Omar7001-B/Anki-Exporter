from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, qconnect, tooltip
from aqt.operations import QueryOp
from anki.collection import Collection
from anki.exporting import AnkiPackageExporter
import os
from datetime import datetime
from typing import Dict, Any
import shutil
import re

# HTML template for the deck index
DECK_INDEX_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{deck_name}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            background-color: #f9f9f9;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{ 
            display: flex;
            margin: 20px 0; 
            border-radius: 8px;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .front, .back {{ 
            flex: 1;
            padding: 20px;
            min-height: 200px;
        }}
        .front {{ 
            background-color: #f8f9fa; 
            border-right: 1px solid #ddd;
        }}
        .back {{ 
            background-color: #fff; 
        }}
        h1 {{ 
            color: #2196F3; 
            border-bottom: 2px solid #2196F3;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .card-count {{ 
            color: #666; 
            margin-bottom: 20px;
            font-size: 0.9em;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 4px;
        }}
        .media-container {{
            margin: 10px 0;
        }}
        .deck-info {{
            margin-bottom: 30px;
            color: #666;
        }}
        .field {{
            margin-bottom: 10px;
        }}
        .field strong {{
            color: #2196F3;
            display: block;
            margin-bottom: 5px;
        }}
        .navigation {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .navigation h2 {{
            color: #2196F3;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        .navigation ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .navigation li {{
            background: #f8f9fa;
            padding: 8px 15px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        .navigation a {{
            color: #2196F3;
            text-decoration: none;
            display: block;
        }}
        .navigation a:hover {{
            text-decoration: underline;
        }}
        .parent-link {{
            margin-bottom: 10px;
        }}
        .parent-link a {{
            color: #666;
            text-decoration: none;
        }}
        .parent-link a:hover {{
            color: #2196F3;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{deck_name}</h1>
        {parent_link}
        <div class="deck-info">
            <div class="card-count">Total Cards: {card_count}</div>
            <div>Export Date: {export_date}</div>
        </div>
        {navigation}
        <div class="cards">
            {cards_html}
        </div>
    </div>
</body>
</html>
"""

# HTML template for each card
CARD_TEMPLATE = """
<div class="card">
    <div class="front">
        {front}
    </div>
    <div class="back">
        {back}
    </div>
</div>
"""

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

def export_deck_to_html(col: Collection, deck_name: str, export_path: str) -> bool:
    """Export a single deck to HTML format."""
    try:
        deck = col.decks.by_name(deck_name)
        if not deck:
            print(f"Could not find deck: {deck_name}")
            return False
        
        # Get deck ID
        did = deck['id']
        
        # First verify if we can find any cards
        card_ids = col.find_cards(f"deck:{deck_name}")
        print(f"Found {len(card_ids)} cards in deck {deck_name}")
        
        # Get direct child decks only
        child_decks = []
        deck_parts = deck_name.split("::")
        deck_parts_count = len(deck_parts)
        
        for d in col.decks.all_names_and_ids():
            # Check if this is a direct child (exactly one level deeper)
            if d.name.startswith(deck_name + "::"):
                child_parts = d.name.split("::")
                if len(child_parts) == deck_parts_count + 1:
                    child_decks.append(d.name)
        
        # Create navigation HTML
        navigation_html = ""
        if child_decks:
            navigation_html = """
            <div class="navigation">
                <h2>Child Decks</h2>
                <ul>
            """
            for child_deck in sorted(child_decks):
                child_name = child_deck.split("::")[-1]
                # Use child_name for the link
                navigation_html += f'<li><a href="{child_name}/index.html">{child_name}</a></li>'
            navigation_html += """
                </ul>
            </div>
            """
        
        # Create parent link HTML
        parent_link_html = ""
        if "::" in deck_name:
            parent_deck_name = deck_name.split("::")[-2]  # Get the parent deck name
            parent_link_html = f'<div class="parent-link"><a href="../index.html">← Back to {parent_deck_name}</a></div>'
        
        if not card_ids:
            # Create empty index if no cards
            cards_html = "<p>No cards in this deck.</p>"
            index_html = DECK_INDEX_TEMPLATE.format(
                deck_name=deck_name,
                card_count=0,
                export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cards_html=cards_html,
                navigation=navigation_html,
                parent_link=parent_link_html
            )
            index_path = os.path.join(export_path, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_html)
            return True

        # Create media directory
        media_dir = os.path.join(export_path, "media")
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            
        collection_media_path = col.media.dir()
        
        # Generate HTML for each card
        cards_html = []
        
        # Process each card
        for card_id in card_ids:
            try:
                card = col.getCard(card_id)
                note = card.note()
                
                # Get template for card
                template = card.template()
                model = note.model()
                
                # Get question and answer content
                front_html = ""
                back_html = ""
                
                # Use direct field content instead of rendered HTML
                fields = dict(note.items())
                field_names = list(fields.keys())
                
                # Split fields between front and back
                for i, (name, value) in enumerate(fields.items()):
                    # Process for media files and update paths for HTML
                    for match in re.findall(r'<img src="([^"]+)"', value):
                        if os.path.exists(os.path.join(collection_media_path, match)):
                            # Copy media file to export media directory
                            src_path = os.path.join(collection_media_path, match)
                            dst_path = os.path.join(media_dir, match)
                            shutil.copy2(src_path, dst_path)
                            
                            # Update path to use relative media directory
                            value = value.replace(f'<img src="{match}"', f'<img src="media/{match}"')
                    
                    # Add field content to appropriate side
                    field_html = f'<div class="field"><strong>{name}</strong>{value}</div>'
                    if i == 0:  # First field goes to front
                        front_html += field_html
                    else:  # All other fields go to back
                        back_html += field_html
                
                # Create card HTML
                card_html = CARD_TEMPLATE.format(
                    front=front_html,
                    back=back_html
                )
                cards_html.append(card_html)
                
            except Exception as e:
                print(f"Error processing card {card_id}: {str(e)}")
                continue

        # Create index.html
        index_html = DECK_INDEX_TEMPLATE.format(
            deck_name=deck_name,
            card_count=len(card_ids),
            export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cards_html="\n".join(cards_html),
            navigation=navigation_html,
            parent_link=parent_link_html
        )
        
        # Write index.html
        index_path = os.path.join(export_path, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_html)
            
        # Verify the file was created
        if not os.path.exists(index_path):
            print(f"Failed to create index.html at {index_path}")
            return False
            
        print(f"Successfully created index.html at {index_path}")
        return True
    except Exception as e:
        print(f"Error exporting {deck_name} to HTML: {str(e)}")
        import traceback
        traceback.print_exc()
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

def export_all_decks_html() -> None:
    """Export all decks to HTML format with folder structure."""
    # Select export directory
    export_path = QFileDialog.getExistingDirectory(mw, "Select Export Directory for HTML")
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
                
                # Export the deck to HTML
                if export_deck_to_html(col, deck_name, deck_path):
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
                        "error": "HTML export failed"
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
        
        message = f"HTML Export complete!\n\n"
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
    tooltip("Starting HTML export...", period=1000)
    
    # Run export in background
    QueryOp(
        parent=mw,
        op=lambda col: do_export(col),
        success=on_success
    ).run_in_background()

# Add menu items
action_export = QAction("Export All Decks (.apkg)", mw)
qconnect(action_export.triggered, export_all_decks)
mw.form.menuTools.addAction(action_export)

action_export_html = QAction("Export All Decks (HTML)", mw)
qconnect(action_export_html.triggered, export_all_decks_html)
mw.form.menuTools.addAction(action_export_html) 