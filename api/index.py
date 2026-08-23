"""
Entry point for Vercel's Python runtime (@vercel/python).

Vercel treats any .py file under /api as a serverless function. When the
module exposes a variable named `app` that is an ASGI application (which
FastAPI is), Vercel's Python builder detects it automatically and wraps it
to run as a serverless function on every request — no extra adapter needed
(unlike the passenger_wsgi.py bridge used for cPanel).

This file just re-exports our real FastAPI app so Vercel can find it.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app  # noqa: E402,F401
