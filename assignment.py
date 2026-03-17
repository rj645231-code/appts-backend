"""
Auto-assignment engine for APPTS.

Strategies
──────────
1. least_loaded  – assign to the engineer with fewest active tasks (default)
2. round_robin   – cycle through eligible engineers in order
3. role_match    – assign to engineer whose department matches task keywords
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from typing import Optional


def _active_task_count(db: Session, user_id: int) -> int:
    return (
        db.query(func.count(models.Task.id))
        .filter(
            models.Task.assigned_to == user_id,
            models.Task.status.in_(["pending", "in_progress"]),
        )
        .scalar()
        or 0
    )


def auto_assign_least_loaded(db: Session, project_id: int) -> Optional[int]:
    """Return user_id of the engineer with the fewest active tasks."""
    engineers = (
        db.query(models.User)
        .filter(models.User.role == "engineer")
        .all()
    )
    if not engineers:
        return None

    best = min(engineers, key=lambda u: _active_task_count(db, u.id))
    return best.id


def auto_assign_round_robin(db: Session, project_id: int, last_assigned_id: Optional[int] = None) -> Optional[int]:
    """Return next engineer in round-robin order."""
    engineers = (
        db.query(models.User)
        .filter(models.User.role == "engineer")
        .order_by(models.User.id)
        .all()
    )
    if not engineers:
        return None

    if last_assigned_id is None:
        return engineers[0].id

    ids = [e.id for e in engineers]
    try:
        idx = ids.index(last_assigned_id)
        return ids[(idx + 1) % len(ids)]
    except ValueError:
        return ids[0]


def auto_assign_role_match(db: Session, task_name: str) -> Optional[int]:
    """
    Simple keyword matching between task_name and user department.
    Falls back to least-loaded if no keyword match.
    """
    keywords = task_name.lower().split()
    engineers = (
        db.query(models.User)
        .filter(models.User.role == "engineer")
        .all()
    )
    for engineer in engineers:
        if engineer.department:
            dept = engineer.department.lower()
            if any(kw in dept for kw in keywords):
                return engineer.id

    # fallback
    return auto_assign_least_loaded(db, project_id=0)


def smart_assign(
    db: Session,
    task_name: str,
    project_id: int,
    strategy: str = "least_loaded",
    last_assigned_id: Optional[int] = None,
) -> Optional[int]:
    """
    Public entry point. strategy: 'least_loaded' | 'round_robin' | 'role_match'
    """
    if strategy == "round_robin":
        return auto_assign_round_robin(db, project_id, last_assigned_id)
    if strategy == "role_match":
        return auto_assign_role_match(db, task_name)
    return auto_assign_least_loaded(db, project_id)
