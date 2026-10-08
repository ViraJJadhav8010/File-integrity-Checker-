import os
import sys

# Ensure project root is in the Python module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app

# Vercel entrypoint for serverless Python runtime
app = app
