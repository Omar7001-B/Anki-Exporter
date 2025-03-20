from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo, qconnect, tooltip
from aqt.operations import QueryOp
from anki.collection import Collection
from typing import Dict, Any
import os
import json

from .exporters.apkg import APKGExporter
from .exporters.html import HTMLExporter

def load_config() -> Dict[str, Any]:
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        return {}

# Load configuration
config = load_config()

def handle_export_result(result: Dict[str, Any], export_type: str) -> None:
    """Handle the result of an export operation."""
    log_file = result.get("log_file")
    success = result.get("success", 0)
    failed = result.get("failed", 0)
    total = result.get("total", 0)
    
    message = f"{export_type} Export complete!\n\n"
    message += f"Successfully exported: {success} of {total} decks\n"
    message += f"Failed: {failed} decks\n"
    
    if log_file and config.get('logging', {}).get('auto_open_log', True):
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

def export_all_decks() -> None:
    """Export all decks to APKG format."""
    export_path = QFileDialog.getExistingDirectory(mw, "Select Export Directory")
    if not export_path:
        return
        
    def do_export(col: Collection) -> Dict[str, Any]:
        exporter = APKGExporter(col)
        return exporter.export_all_decks(export_path)
    
    if config.get('ui', {}).get('show_progress', True):
        tooltip("Starting export...", period=1000)
    QueryOp(
        parent=mw,
        op=lambda col: do_export(col),
        success=lambda result: handle_export_result(result, "APKG")
    ).run_in_background()

def export_all_decks_html() -> None:
    """Export all decks to HTML format."""
    export_path = QFileDialog.getExistingDirectory(mw, "Select Export Directory for HTML")
    if not export_path:
        return
        
    def do_export(col: Collection) -> Dict[str, Any]:
        exporter = HTMLExporter(col)
        return exporter.export_all_decks(export_path)
    
    if config.get('ui', {}).get('show_progress', True):
        tooltip("Starting HTML export...", period=1000)
    QueryOp(
        parent=mw,
        op=lambda col: do_export(col),
        success=lambda result: handle_export_result(result, "HTML")
    ).run_in_background()

# Add menu items
menu_location = config.get('ui', {}).get('menu_location', 'tools')
menu = mw.form.menuTools if menu_location == 'tools' else mw.form.menuFile

action_export = QAction("Export All Decks (.apkg)", mw)
qconnect(action_export.triggered, export_all_decks)
menu.addAction(action_export)

action_export_html = QAction("Export All Decks (HTML)", mw)
qconnect(action_export_html.triggered, export_all_decks_html)
menu.addAction(action_export_html) 