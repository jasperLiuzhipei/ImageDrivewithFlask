"""Flask extensions initialization.

Only initializes core extensions required for the minimal app to run.
"""
from __future__ import annotations
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def init_extensions(app: Flask) -> None:
    """Bind extensions to the app."""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)


__all__ = ["db", "migrate", "jwt", "init_extensions"]
