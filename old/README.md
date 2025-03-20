# Anki Deck Exporter

An Anki add-on that exports all decks in your collection individually as separate .apkg files.

## Features

- Exports each deck as a separate Anki package (.apkg) file
- Preserves scheduling information and media files
- Shows progress during export process
- Includes error handling for failed exports
- Runs exports in the background to prevent UI freezing

## Installation

### From .ankiaddon File (Recommended)

1. Download the `deck_exporter.ankiaddon` file
2. Open Anki and go to Tools > Add-ons > Install from file
3. Select the downloaded .ankiaddon file
4. Restart Anki

### Manual Installation

1. Find your Anki add-ons folder by going to Tools > Add-ons > View Files...
2. Go up one level to reach the `addons21` folder
3. Create a new folder named `deck_exporter`
4. Copy `__init__.py`, `manifest.json`, and `config.json` into this folder
5. Restart Anki

## Usage

1. Open Anki
2. Go to Tools menu
3. Click on "Export All Decks"
4. Select a directory where you want to save the exported decks
5. Wait for the process to complete
6. You'll see a summary of successful and failed exports

## For Developers

### Packaging the Add-on

You can use the included `package_addon.py` script to create an .ankiaddon file:

```bash
python package_addon.py
```

This will create a `deck_exporter.ankiaddon` file that can be installed directly in Anki.

### Anki Compatibility

This add-on is compatible with Anki 2.1.x versions that use PyQt6 (Anki 23.10 and later).

### Add-on Structure

- `__init__.py`: Main add-on code
- `manifest.json`: Add-on metadata
- `config.json`: User configuration options
- `package_addon.py`: Script to create .ankiaddon file

## License

This add-on is released under the MIT License. 