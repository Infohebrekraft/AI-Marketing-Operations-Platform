"""Scheduler foundation for Sprint 3.0.

For production, run scheduled publishing from a dedicated worker process. This file keeps the
interface simple so it can later be connected to Celery Beat or a cloud scheduler.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from .models import GeneratedPost


def due_posts(db: Session, now_iso: str | None = None):
    now_iso = now_iso or datetime.utcnow().isoformat()
    return db.query(GeneratedPost).filter(
        GeneratedPost.status == 'scheduled',
        GeneratedPost.scheduled_time <= now_iso,
    ).all()
