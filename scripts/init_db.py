"""Initialization script to create tables and insert base categories.
Run: `python scripts/init_db.py` after activating environment.
"""
import os
import sys

# Ensure project root is on sys.path when running from scripts/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app, db
from models import Image, User
from utils.auth import hash_password

BASE_CATEGORIES = [
    "flowers", "food", "cars", "dogs", "signs", "buildings", "landscapes", "birds", "electronics", "people"
]


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        # Insert a stub user if none
        if not User.query.first():
            u = User(username="admin", password_hash=hash_password("admin"), role="admin")
            db.session.add(u)
        # Categories currently not a separate table; could refactor later.
        db.session.commit()
    print("Database initialized. Admin user added (username=admin / password=admin). Categories list documented in db_schema.md.")


if __name__ == "__main__":
    main()
