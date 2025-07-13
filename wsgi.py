"""
WSGI config for LuckyDraw application on PythonAnywhere

This module contains the WSGI application used by PythonAnywhere's servers.
"""

import sys
import os

# Add your project directory to sys.path
project_home = '/home/Sarayutp/LuckyDraw'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application

if __name__ == "__main__":
    application.run()