import os
import sys
import subprocess

# Ensure project root on sys.path when executed via conda run
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    print("=== Environment Verification ===")
    print(f"Python: {sys.version}")
    print(f"sys.executable: {sys.executable}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH','')}")
    print(f"CWD: {os.getcwd()}")

    # detect mismatch between pip and python
    try:
        pip_path = subprocess.check_output([sys.executable, '-m', 'pip', 'show', 'flask']).decode().strip()
        print("pip show flask (via current interpreter):\n" + pip_path)
    except subprocess.CalledProcessError as e:
        print("pip show flask failed for current interpreter", e)

    try:
        import flask  # type: ignore
        import PIL  # type: ignore
        import sqlalchemy  # type: ignore
        import werkzeug  # type: ignore

        print(f"Flask: {flask.__version__}")
        print(f"Pillow: {PIL.__version__}")
        print(f"SQLAlchemy: {sqlalchemy.__version__}")
        print(f"Werkzeug: {werkzeug.__version__}")
    except Exception as e:
        print("Import error (likely interpreter mismatch).")
        print("Troubleshooting suggestions:")
        print("  1. Ensure you activated the correct environment: 'conda activate imagedrive313' or source venv.")
        print("  2. Run: python -m pip install -r requirements.txt (forces same interpreter).")
        print("  3. Check which python: 'which python' and 'python -c \"import sys;print(sys.executable)\"'")
        print("  4. If using system Python alias, ensure PATH order prefers conda env bin directory.")
        raise

    # App + DB check
    from app import create_app, db  # noqa: E402

    app = create_app()
    with app.app_context():
        try:
            # ensure folders exist
            up = app.config.get("UPLOAD_FOLDER")
            lg = app.config.get("LOG_DIR")
            os.makedirs(up, exist_ok=True)
            os.makedirs(lg, exist_ok=True)
            # db connectivity (works for sqlite by creating engine)
            conn = db.engine.connect()
            conn.close()
            print("App & DB: OK")
        except Exception as e:
            print("App/DB error:", e)
            raise

    # quick endpoint smoke via test client
    with app.test_client() as c:
        r = c.get('/')
        assert r.status_code == 200, f"Root health not 200: {r.status_code}"
        print("HTTP / :", r.json)

    print("=== Verification PASSED ===")


if __name__ == "__main__":
    main()
