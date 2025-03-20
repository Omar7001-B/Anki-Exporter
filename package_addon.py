#!/usr/bin/env python3
"""
Package Anki Deck Exporter Add-on
This script creates a proper .ankiaddon file from the addon files.
"""

import os
import zipfile
import shutil
import subprocess
import platform
import sys

def package_addon(output_filename="deck_exporter.ankiaddon"):
    """
    Package the add-on into a .ankiaddon file.
    According to Anki docs, the zip should NOT include the top-level folder.
    """
    # Files to include in the package
    files_to_include = [
        "__init__.py",
        "manifest.json",
        "config.json"
    ]
    
    # Create a temporary directory for the files
    if not os.path.exists("temp_package"):
        os.makedirs("temp_package")
    
    # Copy files to the temp directory
    for file in files_to_include:
        if os.path.exists(file):
            shutil.copy(file, os.path.join("temp_package", file))
        else:
            print(f"Warning: {file} not found and will not be included in the package.")
    
    # Create the .ankiaddon zip file
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add each file directly to the zip (not inside a folder)
        for file in os.listdir("temp_package"):
            file_path = os.path.join("temp_package", file)
            if os.path.isfile(file_path):
                # Add the file with its name only (not the path)
                zipf.write(file_path, arcname=os.path.basename(file_path))
    
    # Clean up the temporary directory
    shutil.rmtree("temp_package")
    
    print(f"Add-on packaged successfully as {output_filename}")
    print(f"You can now install it in Anki by going to Tools > Add-ons > Install from file")
    
    # Open the file with the default application
    open_file(output_filename)

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

if __name__ == "__main__":
    package_addon() 