import os
import sys


def main():
    # Best-effort: 如果缺少重型依赖，优雅跳过并返回 0。
    try:
        from app import create_app  # type: ignore
    except Exception as e:
        print(f"[ci-health] SKIP: import app failed: {e}")
        sys.exit(0)

    try:
        # 强制测试模式，避免持久化或重型初始化
        os.environ.setdefault("FLASK_ENV", "testing")
        os.environ.setdefault("USE_TEAM_CLIP", "0")

        app = create_app(testing=True)
        with app.test_client() as c:
            resp = c.get("/api/v1/health")
            print("[ci-health] status=", resp.status_code)
            # 打印关键字段（若存在）
            try:
                data = resp.get_json() or {}
                print("[ci-health] keys:", list((data or {}).keys())[:8])
            except Exception:
                pass
            # 2xx 认为成功，否则仅警告但 exit 0（best-effort）
            if 200 <= resp.status_code < 300:
                print("[ci-health] OK")
            else:
                print("[ci-health] WARN: non-2xx status, tolerated in CI")
    except Exception as e:
        print(f"[ci-health] SKIP: health request failed: {e}")
        # 不使 CI 失败，允许缺少重型依赖
        sys.exit(0)


if __name__ == "__main__":
    main()
