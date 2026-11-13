"""
ProjectVision Flask Application Factory.
Configures middleware, blueprints, templates, and initializes background vision engines.
"""

import logging
from flask import Flask

from core.config import config
from api.routes import api_bp
from services.pipeline_manager import pipeline_manager

logger = logging.getLogger("ProjectVision.App")


def create_app(start_pipelines: bool = True) -> Flask:
    """Creates and configures the Flask application."""
    app = Flask(
        __name__,
        template_folder=str(config.TEMPLATES_FOLDER),
        static_folder=str(config.STATIC_FOLDER)
    )

    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max upload

    # Register blueprints
    app.register_blueprint(api_bp)

    # Initialize and start vision pipelines if requested
    if start_pipelines:
        try:
            logger.info("Starting Vision Pipelines via Application Factory...")
            pipeline_manager.start_all()
        except Exception as e:
            logger.error(f"Error starting pipeline manager during app creation: {e}")

    logger.info("ProjectVision Application successfully created.")
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    app = create_app(start_pipelines=True)
    logger.info(f"Starting ProjectVision Server on http://{config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, threaded=True)

