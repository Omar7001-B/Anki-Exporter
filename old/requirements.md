# Anki Deck Export Add-on Requirements

## Overview
An Anki add-on that automatically exports all decks and their subdecks individually, maintaining the original deck hierarchy structure.

## Functionality Requirements

### 1. Deck Scanning
- Scan all available decks in the user's Anki collection
- Identify the deck hierarchy (main decks and their subdecks)
- Create a list of all decks that need to be exported

### 2. Export Configuration
- Allow user to specify a target export directory
- Support for different export formats:
  - `.apkg` (Anki Package format)
  - `.txt` (Optional: for plain text export)
- Maintain deck names in the exported files

### 3. Export Process
- Export each deck separately as an individual file
- Handle subdecks:
  - Option 1: Export subdecks as part of their parent deck
  - Option 2: Export subdecks as separate files
- Preserve deck hierarchy in the export naming convention
  - Example: "C Sharp Banks::Array" becomes "C Sharp Banks-Array.apkg"

### 4. User Interface
- Add a new menu item under Tools menu
- Provide a simple dialog for:
  - Selecting export directory
  - Choosing export options
  - Showing export progress
- Display completion message with export summary

### 5. Error Handling
- Handle empty decks
- Manage file system errors (permissions, disk space)
- Provide user feedback for any export failures

## Technical Requirements

### Add-on Structure
```python
project_root/
├── __init__.py           # Main add-on entry point
├── manifest.json         # Add-on metadata
├── config.json          # User configuration
├── deck_exporter.py     # Core export functionality
└── gui/                 # UI components
    └── exporter_dialog.py
```

### Dependencies
- Anki 2.1.x compatibility([1](https://addon-docs.ankiweb.net/addon-folders.html))
- Python 3.x
- Standard Anki libraries

### Installation
- Package as `.ankiaddon` file([2](https://addon-docs.ankiweb.net/sharing.html))
- Deployable through AnkiWeb
- Manual installation support

## Limitations and Constraints
- Do not store user data in add-on folder([3](https://addon-docs.ankiweb.net/addon-folders.html))
- Handle large deck collections efficiently
- Consider memory usage during bulk exports
- Respect Anki's add-on guidelines

## Future Enhancements (Optional)
- Custom export naming patterns
- Export scheduling information
- Batch export configurations
- Export format selection per deck
- Progress tracking for large exports 