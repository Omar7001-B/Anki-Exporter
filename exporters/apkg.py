import os
from typing import Dict, Any, List
from .base import BaseExporter

class APKGExporter(BaseExporter):
    def __init__(self, collection):
        super().__init__(collection)
        self.config = self.load_config()
        self.apkg_config = self.config.get('export_options', {}).get('apkg', {})
        
    def export_deck(self, deck_name: str, export_path: str) -> Dict[str, Any]:
        """Export a deck to APKG format."""
        # Prepare export path
        deck_path = self.prepare_export_path(export_path, deck_name)
        
        # Parameters for export
        include_scheduling = self.apkg_config.get('include_scheduling', True)
        include_media = self.apkg_config.get('include_media', True)
        include_tags = self.apkg_config.get('include_tags', True)
        include_deck_config = self.apkg_config.get('include_deck_config', True)
        
        # Get deck
        deck = self.col.decks.get_deck_id(deck_name)
        if not deck:
            return {'success': False, 'error': f'Deck {deck_name} not found'}
        
        # Build the filename with sanitized deck name
        filename = os.path.basename(deck_path) + ".apkg"
        file_path = os.path.join(deck_path, filename)
        
        # Export the deck using anki built-in functions
        try:
            # Get all deck IDs including child decks if needed
            deck_ids = [deck]
            child_decks = self.get_child_decks(deck_name)
            for child in child_decks:
                child_id = self.col.decks.get_deck_id(child)
                if child_id:
                    deck_ids.append(child_id)
            
            # Anki export functions
            from anki.exporting import AnkiPackageExporter
            exporter = AnkiPackageExporter(self.col)
            
            # Set export parameters
            exporter.did = deck
            exporter.includeScheduler = include_scheduling
            exporter.includeSched = include_scheduling  # For compatibility with different Anki versions
            exporter.includeMedia = include_media
            
            # Export to file
            exporter.exportInto(file_path)
            
            return {
                'success': True, 
                'path': file_path,
                'deck_name': deck_name
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Error exporting deck {deck_name}: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return {'success': False, 'error': error_msg}
    
    def export_all_decks(self, export_path: str) -> Dict[str, Any]:
        """Export all decks to APKG format."""
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
                results['failed'] += 1
                results['decks'].append({
                    'name': deck.name,
                    'error': str(e),
                    'success': False
                })
        
        return results 