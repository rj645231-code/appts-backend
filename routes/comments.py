from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_user
import models, schemas

router = APIRouter(prefix="/tasks", tags=["Comments"])


@router.post("/{task_id}/comments", response_model=schemas.CommentOut)
def add_comment(
    task_id: int,
    body: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Engineers can only comment on their own tasks
    if current_user.role == "engineer" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Not your task")

    comment = models.TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        message=body.message,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return schemas.CommentOut(
        id=comment.id,
        task_id=comment.task_id,
        user_id=comment.user_id,
        author_name=current_user.name.strip(),
        author_role=current_user.role,
        message=comment.message,
        created_at=comment.created_at,
    )


@router.get("/{task_id}/comments", response_model=List[schemas.CommentOut])
def get_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comments = (
        db.query(models.TaskComment)
        .filter(models.TaskComment.task_id == task_id)
        .order_by(models.TaskComment.created_at.asc())
        .all()
    )
    result = []
    for c in comments:
        user = db.query(models.User).filter(models.User.id == c.user_id).first()
        result.append(schemas.CommentOut(
            id=c.id,
            task_id=c.task_id,
            user_id=c.user_id,
            author_name=user.name.strip() if user else "Unknown",
            author_role=user.role if user else "unknown",
            message=c.message,
            created_at=c.created_at,
        ))
    return result


@router.delete("/{task_id}/comments/{comment_id}")
def delete_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    comment = db.query(models.TaskComment).filter(
        models.TaskComment.id == comment_id,
        models.TaskComment.task_id == task_id,
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Cannot delete others' comments")
    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}
