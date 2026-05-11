"""
Configuration and launcher for SHL Assessment Recommender.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CATALOG_PATH = PROJECT_ROOT / "shl_product_catalog.json"

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Catalog
CATALOG_RELOAD_INTERVAL = int(os.getenv("CATALOG_RELOAD_INTERVAL", "3600"))  # 1 hour

# Conversation
MAX_TURNS = 8
RECOMMENDATION_LIMIT = 10


if __name__ == "__main__":
    import uvicorn
    from app import app
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level=LOG_LEVEL.lower()
    )
