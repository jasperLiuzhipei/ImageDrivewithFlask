import json
import sys
from importlib import metadata


def try_import(name: str):
    try:
        mod = __import__(name)
        # Prefer importlib.metadata for version to avoid __version__ deprecation
        try:
            ver = metadata.version(name)
        except Exception:
            ver = getattr(mod, "__version__", "unknown")
        return {"present": True, "version": str(ver)}
    except Exception as e:  # broad to show precise error messages
        return {"present": False, "error": f"{type(e).__name__}: {e}"}


def main():
    info = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "modules": {
            "torch": try_import("torch"),
            "faiss": try_import("faiss"),
            "sentence_transformers": try_import("sentence_transformers"),
            "flask": try_import("flask"),
        },
    }
    print(json.dumps(info, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
