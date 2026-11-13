#!/usr/bin/env python3
"""
ProjectVision Application Runner.
Launches the full unified AI multi-stream vision, biometric attendance,
and security command center platform.

Usage:
    python run.py
    python run.py --port 5000 --host 0.0.0.0
"""

import sys
import logging
import argparse

from core.config import config
from api.app import create_app

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    parser = argparse.ArgumentParser(description="ProjectVision Command Center")
    parser.add_argument("--host", type=str, default=config.HOST, help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=config.PORT, help="Port to listen on (default: 5000)")
    parser.add_argument("--debug", action="store_true", default=config.DEBUG, help="Run in debug mode")
    parser.add_argument("--no-pipelines", action="store_true", help="Launch without starting camera pipelines immediately")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")
    args = parser.parse_args()

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger("ProjectVision")

    print("""
    ========================================================================
     ____            _           _  __     ___     _             
    |  _ \ _ __ ___ (_) ___  ___| |_\ \   / (_)___(_) ___  _ __  
    | |_) | '__/ _ \| |/ _ \/ __| __|\ \ / /| / __| |/ _ \| '_ \ 
    |  __/| | | (_) | |  __/ (__| |_  \ V / | \__ \ | (_) | | | |
    |_|   |_|  \___// |\___|\___|\__|  \_/  |_|___/_|\___/|_| |_|
                  |__/                                            
     Comprehensive Multi-Stream Intelligent Vision & Security Platform
     Version 2.0 (Autonomous Production Architecture)
    ========================================================================
    """)

    logger.info(f"Initializing ProjectVision Server...")
    logger.info(f"Binding to http://{args.host}:{args.port}")
    logger.info(f"Dashboard available at: http://localhost:{args.port}/")
    logger.info(f"Camera Grid available at: http://localhost:{args.port}/grid")
    logger.info(f"Speech Notes available at: http://localhost:{args.port}/notes")
    logger.info(f"Blockchain Ledger at: http://localhost:{args.port}/blockchain")

    app = create_app(start_pipelines=not args.no_pipelines)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

if __name__ == '__main__':
    main()

