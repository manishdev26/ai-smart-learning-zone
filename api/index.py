import sys
import os

# Add project root to path so app.py can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, init_db

# Initialize DB on every cold start (uses /tmp on Vercel)
init_db()

# Vercel expects the WSGI app to be named 'app'
