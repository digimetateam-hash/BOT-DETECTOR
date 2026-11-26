"""
File entry point utama untuk Streamlit Community Cloud.
Merujuk langsung ke app/main.py
"""
import os
import sys

# Tambahkan direktori root ke sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import *
