import os
import shutil
import re
from typing import List, Dict, Any, Tuple
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
        """Load HTML templates and styles from files."""
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        
        try:
            # Load deck template
            with open(os.path.join(template_dir, 'deck.html'), 'r', encoding='utf-8') as f:
                self.deck_template = f.read()
            
            # Load card template
            with open(os.path.join(template_dir, 'card.html'), 'r', encoding='utf-8') as f:
                self.card_template = f.read()
                
            # Load styles
            with open(os.path.join(template_dir, 'styles.css'), 'r', encoding='utf-8') as f:
                styles = f.read()
                
            # Escape CSS curly braces by doubling them
            escaped_styles = styles.replace('{', '{{').replace('}', '}}')
                
            # Create a style tag with the escaped CSS content
            style_tag = f'<style type="text/css">\n{escaped_styles}\n</style>'
            
            # Find the closing head tag and insert styles before it
            head_close_pos = self.deck_template.find('</head>')
            if head_close_pos == -1:
                raise Exception("Could not find </head> tag in deck template")
                
            self.deck_template = (
                self.deck_template[:head_close_pos] + 
                style_tag +
                self.deck_template[head_close_pos:]
            )
            
        except Exception as e:
            print(f"Error loading templates: {e}")
            import traceback
            traceback.print_exc()
            raise Exception("Failed to load templates. Please ensure all template files exist in the templates directory.")

    def process_media_files(self, content: str, media_dir: str, collection_media_path: str) -> str:
        """Process media files in the content and copy them to the media directory."""
        try:
            # Find all image tags
            pictures = re.findall(r'\<img src="([^"]+)"', content)
            if pictures:
                value = ""
                for pic in pictures:
                    src_path = os.path.join(collection_media_path, pic)
                    if os.path.exists(src_path):
                        # Copy media file to export media directory
                        dst_path = os.path.join(media_dir, pic)
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                        # Create image tag with relative path
                        value += f'<img src="media/{pic}">'
                return value if value else content
        except Exception as e:
            print(f"Warning: Error processing media file: {e}")
        return content

    def get_cards(self, deck_name: str, sort_field: str = None, ascending: bool = True) -> List:
        """Get all cards from a deck, optionally sorted by field."""
        cards = []
        try:
            # Get deck and its children
            deck = self.col.decks.by_name(deck_name)
            if not deck:
                return cards

            decks = [deck_name]
            children = self.col.decks.children(deck['id'])
            if children:
                decks.extend([name for (name, _) in children])

            # Get cards from all decks
            for d in decks:
                query = f'deck:"{d}"'
                card_ids = self.col.find_cards(query)
                for cid in card_ids:
                    card = self.col.get_card(cid)
                    cards.append(card)

            # Sort cards if requested
            if sort_field:
                cards.sort(
                    key=lambda c: c.due if sort_field == 'Due' else c.note().get(sort_field, ''),
                    reverse=not ascending
                )

        except Exception as e:
            print(f"Error getting cards: {e}")
        return cards

    def get_child_decks(self, deck_name: str) -> List[str]:
        """Get all direct child decks of the given deck."""
        child_decks = []
        try:
            deck = self.col.decks.by_name(deck_name)
            if deck:
                children = self.col.decks.children(deck['id'])
                if children:
                    child_decks = [name for (name, _) in children]
        except Exception as e:
            print(f"Warning: Error getting child decks: {e}")
        return child_decks

    def get_parent_deck(self, deck_name: str) -> Tuple[str, str]:
        """Get parent deck name and create parent link HTML."""
        if "::" not in deck_name:
            return None, ""
            
        parent_deck_name = deck_name.split("::")[-2]
        parent_link_html = f'<div class="parent-link"><a href="../index.html">← Back to {parent_deck_name}</a></div>'
        return parent_deck_name, parent_link_html

    def export_deck(self, deck_name: str, export_path: str) -> Dict[str, Any]:
        """Export a deck to HTML format."""
        try:
            # Create folder structure
            deck_path = create_folder_structure(export_path, deck_name)
            
            # Get cards
            cards = self.get_cards(deck_name)
            if not cards:
                print(f"No cards found in deck: {deck_name}")
                return {'success': False, 'error': 'No cards found'}

            # Create media directory
            media_dir = ensure_media_directory(deck_path, 'media')
            collection_media_path = self.col.media.dir()

            # Generate HTML for each card
            cards_html = []
            dedup = set()  # For deduplication

            for i, card in enumerate(cards):
                try:
                    note = card.note()
                    fields = dict(note.items())
                    
                    # Skip if we've seen this card before
                    key = "".join(str(v) for v in fields.values())
                    if key in dedup:
                        continue
                    dedup.add(key)

                    # Process fields
                    field_items = list(fields.items())
                    if not field_items:
                        continue

                    # First field goes to front
                    front_html = ""
                    name, value = field_items[0]
                    value = self.process_media_files(value, media_dir, collection_media_path)
                    if value.strip():
                        front_html = f'<div class="field"><strong>{name}</strong>{value}</div>'

                    # Rest of fields go to back
                    back_html = ""
                    for name, value in field_items[1:]:
                        value = self.process_media_files(value, media_dir, collection_media_path)
                        if value.strip():
                            back_html += f'<div class="field"><strong>{name}</strong>{value}</div>'

                    # Skip empty cards
                    if not front_html.strip() and not back_html.strip():
                        continue

                    # Create card HTML
                    card_html = self.card_template.format(
                        front=front_html or '<div class="field">(Empty)</div>',
                        back=back_html or '<div class="field">(Empty)</div>'
                    )
                    cards_html.append(card_html)

                except Exception as e:
                    print(f"Warning: Error processing card {card.id}: {str(e)}")
                    continue

            if not cards_html:
                print(f"No valid cards to export in deck: {deck_name}")
                return {'success': False, 'error': 'No valid cards to export'}

            # Create navigation
            child_decks = self.get_child_decks(deck_name)
            navigation_html = self._create_navigation_html(child_decks)
            _, parent_link_html = self.get_parent_deck(deck_name)

            # Create index.html
            index_html = self.deck_template.format(
                deck_name=deck_name,
                card_count=len(cards_html),
                export_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                cards_html="\n".join(cards_html),
                navigation=navigation_html,
                parent_link=parent_link_html
            )

            # Write index.html
            index_path = os.path.join(deck_path, "index.html")
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_html)

            print(f"Successfully exported deck {deck_name} with {len(cards_html)} cards")
            return {
                'success': True,
                'path': deck_path,
                'card_count': len(cards_html)
            }

        except Exception as e:
            error_msg = f"Error exporting deck {deck_name}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': error_msg}

    def export_all_decks(self, export_path: str) -> Dict[str, Any]:
        """Export all decks to HTML format."""
        results = {
            'success': 0,
            'failed': 0,
            'total': 0,
            'decks': []
        }
        
        try:
            # Get all deck names
            deck_names = self.col.decks.all_names_and_ids()
            results['total'] = len(deck_names)
            
            print(f"Found {len(deck_names)} decks to export")
            
            # Sort decks to ensure parents are created before children
            sorted_decks = sorted(deck_names, key=lambda x: len(x.name.split("::")))
            
            # Export each deck
            for deck in sorted_decks:
                try:
                    print(f"Exporting deck: {deck.name}")
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
                    print(f"Error exporting deck {deck.name}: {str(e)}")
                    results['failed'] += 1
                    results['decks'].append({
                        'name': deck.name,
                        'error': str(e),
                        'success': False
                    })
            
            print(f"Export complete. Success: {results['success']}, Failed: {results['failed']}")
            return results
            
        except Exception as e:
            print(f"Critical error during export: {str(e)}")
            import traceback
            traceback.print_exc()
            return results

    def _create_navigation_html(self, child_decks: List[str]) -> str:
        """Create navigation HTML for child decks."""
        if not child_decks:
            return ""

        navigation_html = '<div class="navigation"><h2>Child Decks</h2><ul>'
        for child_deck in sorted(child_decks):
            child_name = child_deck.split("::")[-1]
            navigation_html += f'<li><a href="{child_name}/index.html">{child_name}</a></li>'
        navigation_html += '</ul></div>'
        
        return navigation_html 