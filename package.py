#!/usr/bin/env python3
"""
Package Anki Deck Exporter Add-on
This script creates a proper .ankiaddon file and can install it directly in Anki.

Usage:
  python package.py           - Package the addon and save in the build folder
  python package.py -i        - Package the addon, save in the build folder, and install in Anki
  python package.py --install - Package the addon, save in the build folder, and install in Anki
  python package.py -l        - List the addon structure
  python package.py --list    - List the addon structure
"""

import os
import zipfile
import shutil
import subprocess
import platform
import sys
import tempfile

def get_anki_addon_folder():
    """Get the Anki addons folder based on the operating system."""
    if platform.system() == 'Windows':
        return os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Anki2', 'addons21')
    elif platform.system() == 'Darwin':  # macOS
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Anki2', 'addons21')
    else:  # Linux and other Unix-like
        return os.path.join(os.path.expanduser('~'), '.local', 'share', 'Anki2', 'addons21')

def get_addon_id():
    """Get the addon ID from the manifest.json file or user input."""
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.json')
    if os.path.exists(manifest_path):
        try:
            import json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                # Check if manifest has an ID field
                if 'id' in manifest:
                    return manifest['id']
        except Exception as e:
            print(f"Error reading manifest.json: {e}")
    
    # If we get here, either no manifest or no ID in manifest
    addon_id = input("Enter the addon ID (if you have one) or leave blank to generate: ").strip()
    if not addon_id:
        import uuid
        addon_id = str(uuid.uuid4()).replace('-', '')
        print(f"Generated new addon ID: {addon_id}")
    return addon_id

def package_addon(output_path=None, install=False):
    """
    Package the add-on into a .ankiaddon file.
    According to Anki docs, the zip should NOT include the top-level folder.
    """
    # Get current directory (where the add-on is located)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Create build directory if it doesn't exist
    build_dir = os.path.join(current_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    if output_path is None:
        output_path = os.path.join(build_dir, "deck_exporter.ankiaddon")
    
    print(f"Packaging addon from: {current_dir}")
    print(f"Output file will be: {output_path}")
    
    # Create a list of excluded files and directories
    excluded = [
        '__pycache__',
        'package.py',
        '.git',
        '.gitignore',
        'build',
        'deck_exporter.ankiaddon',
        'test',
        'old'
    ]
    
    # Get all files in the current directory recursively
    files_to_include = []
    for root, dirs, files in os.walk(current_dir):
        # Remove excluded directories from the dirs list
        dirs[:] = [d for d in dirs if d not in excluded]
        
        for file in files:
            # Skip excluded files
            if file in excluded or file.endswith('.pyc'):
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, current_dir)
            files_to_include.append((full_path, rel_path))
    
    # Create a temporary directory for packaging
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the .ankiaddon zip file
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all directories first
            dirs_added = set()
            for full_path, rel_path in files_to_include:
                dir_path = os.path.dirname(rel_path)
                if dir_path:
                    dir_parts = dir_path.split(os.sep)
                    current = ""
                    for part in dir_parts:
                        if current:
                            current = os.path.join(current, part)
                        else:
                            current = part
                            
                        if current not in dirs_added:
                            zipf.writestr(current + '/', '')
                            dirs_added.add(current)
            
            # Now add all files
            for full_path, rel_path in files_to_include:
                zipf.write(full_path, rel_path)
    
    print(f"Add-on packaged successfully with {len(files_to_include)} files")
    
    # Install the addon if requested
    if install:
        install_addon(output_path)
    else:
        # Open the file with the default application
        open_file(output_path)
        print(f"Add-on packaged in {output_path}")
        print(f"You can now install it in Anki by going to Tools > Add-ons > Install from file")

def install_addon(addon_path):
    """Install the add-on directly in Anki."""
    addon_id = get_addon_id()
    anki_addons_folder = get_anki_addon_folder()
    
    if not os.path.exists(anki_addons_folder):
        print(f"Anki addons folder not found at {anki_addons_folder}")
        print("Please make sure Anki is installed on your system.")
        return False
    
    addon_folder = os.path.join(anki_addons_folder, addon_id)
    
    # Remove existing addon if it exists
    if os.path.exists(addon_folder):
        try:
            shutil.rmtree(addon_folder)
            print(f"Removed existing addon at {addon_folder}")
        except Exception as e:
            print(f"Error removing existing addon: {e}")
            print("Please close Anki and try again.")
            return False
    
    # Extract the addon to the addons folder
    try:
        os.makedirs(addon_folder, exist_ok=True)
        with zipfile.ZipFile(addon_path, 'r') as zipf:
            zipf.extractall(addon_folder)
        print(f"Addon installed successfully at {addon_folder}")
        
        # Write a meta.json file to include the addon ID
        meta_path = os.path.join(anki_addons_folder, f"{addon_id}.json")
        import json
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({"name": "Deck Exporter", "mod": 0}, f)
        
        print("Restart Anki to use the addon.")
        return True
    except Exception as e:
        print(f"Error installing addon: {e}")
        return False

def open_file(file_path):
    """Open a file with the default associated application"""
    try:
        if platform.system() == 'Windows':
            os.startfile(file_path)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        else:  # Linux and other Unix-like
            subprocess.call(['xdg-open', file_path])
        print(f"Opened {file_path} with the default application")
    except Exception as e:
        print(f"Error opening the file: {e}")
        print(f"Please manually open {os.path.abspath(file_path)}")

def list_addon_structure():
    """Display the structure of the addon being packaged"""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    print(f"Addon directory structure for: {current_dir}")
    print("=" * 50)
    
    excluded = ['__pycache__', '.git', '.gitignore', 'build']
    
    def print_dir(path, prefix=""):
        items = os.listdir(path)
        items = [item for item in items if item not in excluded and not item.endswith('.pyc')]
        items.sort()
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            item_path = os.path.join(path, item)
            
            if is_last:
                print(f"{prefix}└── {item}")
                new_prefix = prefix + "    "
            else:
                print(f"{prefix}├── {item}")
                new_prefix = prefix + "│   "
                
            if os.path.isdir(item_path) and item not in excluded:
                print_dir(item_path, new_prefix)
    
    print_dir(current_dir)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-l', '--list']:
            list_addon_structure()
        elif sys.argv[1] in ['-i', '--install']:
            package_addon(install=True)
        else:
            print("Unknown option. Available options:")
            print("  -l, --list    : List addon structure")
            print("  -i, --install : Package and install addon in Anki")
            print("  No option     : Just package the addon")
    else:
        package_addon() 