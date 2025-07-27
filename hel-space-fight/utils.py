
# utils.py
import os
import sys

def get_asset_path(filename):
    if hasattr(sys, '_MEIPASS'):
        # Running from PyInstaller bundle
        path = os.path.join(sys._MEIPASS, 'assets', filename)
    else:
        # Running from source
        path = os.path.join('assets', filename)
    # print(f"DEBUG: Attempting to load asset: {path}") # Keep for debugging if needed
    return path
