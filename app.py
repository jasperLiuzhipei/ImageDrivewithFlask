from flask import Flask, jsonify
from config import Config
from logging_config import configure_logging
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    configure_logging(app)
    db.init_app(app)

    from blueprints.auth import auth_bp
    from blueprints.files import files_bp
    from blueprints.images import images_bp
    from blueprints.search import search_bp
    from blueprints.processing import processing_bp
    from blueprints.analytics import analytics_bp
    from blueprints.web import web_bp
    from blueprints.users import users_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(files_bp, url_prefix="/api/files")
    app.register_blueprint(images_bp, url_prefix="/api/images")
    app.register_blueprint(search_bp, url_prefix="/api/search")
    app.register_blueprint(processing_bp, url_prefix="/api/process")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(web_bp, url_prefix="/web")

    @app.route('/')
    def index():
        return jsonify({"status": "ok", "message": "WebImageDrive Flask API"}), 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
