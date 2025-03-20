# Deck Exporter Configuration

This document describes the configuration options available in `config.json`.

## Export Options

### APKG Export
- `include_scheduling`: Include card scheduling information
- `include_media`: Include media files in the export
- `include_tags`: Include card tags in the export
- `include_deck_config`: Include deck configuration settings

### HTML Export
- `include_media`: Include media files in the export
- `split_screen`: Display front and back of cards side by side
- `show_field_names`: Show field names in the HTML output
- `max_width`: Maximum width of the content container (in pixels)
- `theme`: Visual theme for the HTML export ("light" or "dark")
- `navigation_style`: Style of the navigation menu ("modern" or "classic")

## Folder Structure
- `sanitize_names`: Clean folder names by removing special characters
- `allowed_chars`: Characters allowed in folder names
- `max_depth`: Maximum depth of nested deck folders

## Media Settings
- `copy_media`: Copy media files to the export directory
- `media_folder`: Name of the folder for media files
- `max_image_size`: Maximum width/height for images (in pixels)
- `image_quality`: JPEG quality for image compression (0-100)

## Logging
- `create_hierarchy_log`: Create a log file showing deck hierarchy
- `log_level`: Level of logging ("debug", "info", "warning", "error")
- `save_export_history`: Keep track of previous exports

## User Interface
- `show_progress`: Show progress during export
- `auto_open_log`: Automatically open the log file after export
- `menu_location`: Location of the add-on menu items ("tools" or "file")

## Example Configuration

```json
{
    "export_options": {
        "apkg": {
            "include_scheduling": true,
            "include_media": true,
            "include_tags": true,
            "include_deck_config": true
        },
        "html": {
            "include_media": true,
            "split_screen": true,
            "show_field_names": true,
            "max_width": 1200,
            "theme": "light",
            "navigation_style": "modern"
        }
    }
}
``` 