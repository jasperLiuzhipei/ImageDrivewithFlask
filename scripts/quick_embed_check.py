from __future__ import annotations
import os
import json

from app import create_app
from app.services import clip_runtime


def main():
    app = create_app()
    with app.app_context():
        cfg_backend = app.config.get("USE_TEAM_CLIP")
        print(f"USE_TEAM_CLIP cfg={cfg_backend}")
        print(f"TEAM_CLIP_PROCESSOR_PATH={app.config.get('TEAM_CLIP_PROCESSOR_PATH','')}")

        print("embedding_backend_config:", "team-processor" if cfg_backend else "sentence-transformers")
        print("embedding_backend_loaded(before):", clip_runtime.embedding_backend())
        print("embedding_dim(before):", clip_runtime.embedding_dim())

        try:
            tv = clip_runtime.embed_text("hello world")
            print("embed_text length:", None if tv is None else len(tv))
        except Exception as e:
            print("embed_text exception:", e)

        try:
            iv = clip_runtime.embed_image_path(os.path.join("samples", "a.png"))
            print("embed_image length:", None if iv is None else len(iv))
        except Exception as e:
            print("embed_image exception:", e)

        print("embedding_backend_loaded(after):", clip_runtime.embedding_backend())
        print("embedding_dim(after):", clip_runtime.embedding_dim())


if __name__ == "__main__":
    main()
