from __future__ import annotations
"""Reset a user's password in the local dev DB.

Usage:
  python3 -m scripts.reset_password --username demo --password password
"""
import os
import sys
import argparse


# Ensure project root on sys.path when run as a script
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import User  # noqa: E402
import bcrypt  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Reset a user's password")
    parser.add_argument("--username", required=True, help="username to reset")
    parser.add_argument("--password", required=True, help="new plaintext password")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=args.username).first()
        if not user:
            print(f"User '{args.username}' not found")
            sys.exit(2)
        hashed = bcrypt.hashpw(args.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password_hash = hashed
        db.session.commit()
        print(f"Password for '{args.username}' has been reset.")


if __name__ == "__main__":
    main()
