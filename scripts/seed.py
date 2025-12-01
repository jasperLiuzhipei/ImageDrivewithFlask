"""Seed script (draft): create a demo user and a few image placeholders.
Run with: python scripts/seed.py
"""
from __future__ import annotations
import os
import sys

# Ensure project root is on sys.path when running as: python scripts/seed.py
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app
from app.extensions import db
from app.models import User, Image


def get_or_create(model, defaults=None, **kwargs):
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    params = dict(kwargs)
    if defaults:
        params.update(defaults)
    instance = model(**params)
    db.session.add(instance)
    return instance, True


def main():
    app = create_app()
    with app.app_context():
        db.create_all()  # ensure tables exist (dev convenience)

        # set hashed passwords
        try:
            import bcrypt
            demo_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8")
            admin_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8")
        except Exception:
            demo_hash = "<hashed>"
            admin_hash = "<hashed>"

        # demo user
        user, _ = get_or_create(User, username="demo", defaults={"password_hash": demo_hash})
        # admin user (persisted default admin/admin)
        admin_user, created_admin = get_or_create(User, username="admin", defaults={"password_hash": admin_hash})
        # Ensure user.id is assigned before using in foreign keys
        db.session.flush()

        # Placeholder images (ensure owner_id present)
        for i in range(1, 4):
            get_or_create(
                Image,
                owner_id=user.id,
                original_filename=f"sample_{i}.jpg",
                storage_uri=f"local://sample_{i}.jpg",
                status="READY",
                visibility="private",
            )

        db.session.commit()
        print("Seed completed. demo id:", user.id, "admin id:", admin_user.id)


if __name__ == "__main__":
    main()
