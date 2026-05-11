#!/usr/bin/env python
"""
Startup script for SHL Assessment Recommender.
Run this to start the FastAPI server.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Start the FastAPI server."""
    logger.info("Starting SHL Assessment Recommender...")
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    try:
        # Import and configure
        from config import API_HOST, API_PORT, LOG_LEVEL
        import uvicorn
        from app import app
        
        logger.info(f"Starting server on {API_HOST}:{API_PORT}")
        logger.info(f"Log level: {LOG_LEVEL}")
        logger.info("Swagger UI available at: http://localhost:8000/docs")
        
        # Run server
        uvicorn.run(
            app,
            host=API_HOST,
            port=API_PORT,
            log_level=LOG_LEVEL.lower()
        )
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
