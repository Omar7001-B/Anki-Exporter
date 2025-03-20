import os
from typing import List, Dict, Any
from datetime import datetime
from ..utils.files import (
    create_folder_structure,
    process_media_files,
    ensure_media_directory
)
from .base import BaseExporter

class HTMLExporter(BaseExporter):
    """
    HTML exporter class that handles the export of decks to HTML format.
    """
    
    def __init__(self, collection):
        super().__init__(collection)
        self.config = self.load_config()
        self.html_config = self.config.get('html_export', {})
        self.load_templates()

    def load_templates(self):
        """Load HTML templates from files."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        
        try:
            with open(os.path.join(template_dir, 'deck.html'), 'r', encoding='utf-8') as f:
                self.deck_template = f.read()
                
            with open(os.path.join(template_dir, 'card.html'), 'r', encoding='utf-8') as f:
                self.card_template = f.read()
        except Exception as e:
            print(f"Error loading templates: {e}")
            # Fallback to embedded templates
            self.deck_template = self._get_default_deck_template()
            self.card_template = self._get_default_card_template()

    def export_deck(self, deck_name: str, export_path: str) -> Dict[str, Any]:
        """Export a deck to HTML format."""
        try:
            # Prepare export path
            deck_path = create_folder_structure(
                export_path,
                deck_name,
                sanitize=self.config.get('folder_structure', {}).get('sanitize', True),
                allowed_chars=self.config.get('folder_structure', {}).get('allowed_chars', [' ', '-', '_']),
                max_depth=self.config.get('folder_structure', {}).get('max_depth', 10)
            )
            
            # Get deck info
            deck = self.col.decks.by_name(deck_name)
            if not deck:
                return {'success': False, 'error': f'Deck {deck_name} not found'}
                
            # Get card IDs
            card_ids = self.col.find_cards(f'deck:"{deck_name}"')
            
            # Create navigation and parent links
            child_decks = self.get_child_decks(deck_name)
            navigation_html = self._create_navigation_html(child_decks)
            parent_name, parent_link_html = self.get_parent_deck(deck_name)
            
            # Create media directory
            media_dir = ensure_media_directory(
                deck_path,
                media_folder=self.config.get('media', {}).get('media_folder', 'media')
            )
            collection_media_path = self.col.media.dir()
            
            if not card_ids:
                # Create empty index if no cards
                cards_html = "<p>No cards in this deck.</p>"
                index_html = self.deck_template.format(
                    deck_name=deck_name,
                    card_count=0,
                    export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    cards_html=cards_html,
                    navigation=navigation_html,
                    parent_link=parent_link_html
                )
                index_path = os.path.join(deck_path, "index.html")
                with open(index_path, "w", encoding="utf-8") as f:
                    f.write(index_html)
                return {
                    'success': True,
                    'path': deck_path,
                    'card_count': 0
                }
            
            # Generate HTML for each card
            split_screen = self.html_config.get('split_screen', True)
            show_field_names = self.html_config.get('show_field_names', True)
            cards_html = []
            
            for card_id in card_ids:
                try:
                    card = self.col.getCard(card_id)
                    note = card.note()
                    
                    # Get field content
                    fields = dict(note.items())
                    front_html = ""
                    back_html = ""
                    
                    # Split fields between front and back
                    for i, (name, value) in enumerate(fields.items()):
                        # Process media in content
                        value = process_media_files(
                            value,
                            media_dir,
                            collection_media_path,
                            max_image_size=self.config.get('media', {}).get('max_image_size', 1920),
                            image_quality=self.config.get('media', {}).get('image_quality', 85)
                        )
                        
                        # Add field content to appropriate side
                        if show_field_names:
                            field_html = f'<div class="field"><strong>{name}</strong>{value}</div>'
                        else:
                            field_html = f'<div class="field">{value}</div>'
                            
                        if i == 0:  # First field goes to front
                            front_html += field_html
                        else:  # All other fields go to back
                            back_html += field_html
                    
                    # Create card HTML
                    card_html = self.card_template.format(
                        front=front_html,
                        back=back_html
                    )
                    cards_html.append(card_html)
                    
                except Exception as e:
                    print(f"Error processing card {card_id}: {str(e)}")
                    continue
            
            # Create index.html
            index_html = self.deck_template.format(
                deck_name=deck_name,
                card_count=len(card_ids),
                export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cards_html="\n".join(cards_html),
                navigation=navigation_html,
                parent_link=parent_link_html
            )
            
            # Write index.html
            index_path = os.path.join(deck_path, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_html)
            
            return {
                'success': True,
                'path': deck_path,
                'card_count': len(card_ids)
            }
        except Exception as e:
            import traceback
            error_msg = f"Error exporting deck {deck_name}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return {'success': False, 'error': error_msg}

    def export_all_decks(self, export_path: str) -> Dict[str, Any]:
        """Export all decks to HTML format."""
        results = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'decks': []
        }
        
        # Get all deck names
        deck_names = self.col.decks.all_names_and_ids()
        results['total'] = len(deck_names)
        
        # Create log file for deck hierarchy
        results['log_file'] = self.create_log_file(export_path)
        
        # Export each deck
        for deck in deck_names:
            try:
                result = self.export_deck(deck.name, export_path)
                if result.get('success', False):
                    results['success'] += 1
                    results['decks'].append({
                        'name': deck.name,
                        'path': result.get('path', ''),
                        'card_count': result.get('card_count', 0),
                        'success': True
                    })
                else:
                    results['failed'] += 1
                    results['decks'].append({
                        'name': deck.name,
                        'error': result.get('error', 'Unknown error'),
                        'success': False
                    })
            except Exception as e:
                import traceback
                error_msg = f"Error exporting deck {deck.name}: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                results['failed'] += 1
                results['decks'].append({
                    'name': deck.name,
                    'error': error_msg,
                    'success': False
                })
        
        return results
        
    def _create_navigation_html(self, child_decks: List[str]) -> str:
        """Create navigation HTML for child decks."""
        if not child_decks:
            return ""

        navigation_html = '<div class="navigation"><h3>Child Decks</h3><ul>'
        for child_deck in sorted(child_decks):
            child_name = child_deck.split("::")[-1]
            navigation_html += f'<li><a href="{child_name}/index.html">{child_name}</a></li>'
        navigation_html += '</ul></div>'
        
        return navigation_html
        
    def _get_default_deck_template(self) -> str:
        """Get the default deck template."""
        return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{deck_name} - Anki Deck Export</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .navigation {
            background: white;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .navigation ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .navigation li {
            margin: 0;
        }
        .navigation a {
            display: inline-block;
            padding: 8px 16px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.2s;
        }
        .navigation a:hover {
            background: #0056b3;
        }
        .parent-link {
            margin-bottom: 20px;
        }
        .parent-link a {
            color: #007bff;
            text-decoration: none;
        }
        .parent-link a:hover {
            text-decoration: underline;
        }
        .card {
            display: flex;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .front, .back {
            flex: 1;
            padding: 20px;
        }
        .front {
            background: #f8f9fa;
            border-right: 1px solid #ddd;
        }
        .back {
            background: white;
        }
        .field {
            margin-bottom: 10px;
        }
        .field strong {
            display: block;
            margin-bottom: 5px;
            color: #666;
        }
        img {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        {parent_link}
        {navigation}
        <h1>{deck_name}</h1>
        <p>Total Cards: {card_count}</p>
        <p>Export Date: {export_date}</p>
        <div class="cards">
            {cards_html}
        </div>
    </div>
</body>
</html>'''
        
    def _get_default_card_template(self) -> str:
        """Get the default card template."""
        return '''<div class="card">
    <div class="front">
        {front}
    </div>
    <div class="back">
        {back}
    </div>
</div>''' 