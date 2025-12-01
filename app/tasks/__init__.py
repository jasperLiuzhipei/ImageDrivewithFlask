"""Task registration entrypoint (optional for Celery wiring).

In a future step, call init_celery(celery_app) to attach tasks.
"""

try:
	from .placeholders import init_celery  # type: ignore
except Exception:  # pragma: no cover - placeholder
	def init_celery(app):  # type: ignore
		return None

__all__ = ["init_celery"]
