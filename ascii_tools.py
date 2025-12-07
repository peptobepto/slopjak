# File: ascii_tools.py
"""ASCII art utilities for splash screens and animations."""

import time
import threading

# Simple ASCII art logo
ascii_art = """
╔═══════════════════════════════════════╗
║             SLOPJAK v1.0              ║
║ AI-powered YouTube shitslop Generator ║
║               kill me                 ║
╚═══════════════════════════════════════╝
"""


def splash_screen(art_text):
    """Display a splash screen with ASCII art."""
    print("\n" * 2)
    print(art_text)
    print("\n" * 2)


def play_ascii_gif_threaded(art_frames, delay=0.1):
    """Play an ASCII animation in a separate thread (placeholder)."""
    # Placeholder implementation
    pass

