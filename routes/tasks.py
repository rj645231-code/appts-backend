from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from auth import get_current_user, require_role
import models, schemas
from assignment import smart_assign
from datetime import datetime

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=schemas.TaskOut)
def create_task(
    task: schemas.TaskCreate,
    strategy: str = Query("least_loaded", description="auto-assign strategy: least_loaded | round_robin | role_match"),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    """
    Create a task. If assigned_to is omitted, the system auto-assigns
    using the selected strategy.
    """
    assigned_to = task.assigned_to
    if assigned_to is None:
        # find last assigned for round-robin
        last = (
            db.query(models.Task)
            .filter(models.Task.project_id == task.project_id)
            .order_by(models.Task.id.desc())
            .first()
        )
        last_id = last.assigned_to if last else None
        assigned_to = smart_assign(db, task.task_name, task.project_id, strategy, last_id)

    new_task = models.Task(
        task_name=task.task_name,
        description=task.description,
        project_id=task.project_id,
        assigned_to=assigned_to,
        priority=task.priority,
        deadline=task.deadline,
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # audit log entry for creation
    log = models.TaskLog(
        task_id=new_task.id,
        changed_by=current_user.id,
        new_status="pending",
        new_progress=0,
        note=f"Task created and auto-assigned via strategy '{strategy}'" if not task.assigned_to else "Task created",
    )
    db.add(log)
    db.commit()

    return new_task


@router.get("/", response_model=List[schemas.TaskOut])
def list_tasks(
    project_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    q = db.query(models.Task)
    if project_id:
        q = q.filter(models.Task.project_id == project_id)
    if assigned_to:
        q = q.filter(models.Task.assigned_to == assigned_to)
    if status:
        q = q.filter(models.Task.status == status)
    # engineer sees only their tasks
    if current_user.role == "engineer":
        q = q.filter(models.Task.assigned_to == current_user.id)
    return q.all()


@router.get("/my", response_model=List[schemas.TaskOut])
def my_tasks(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Engineer: fetch own tasks."""
    return db.query(models.Task).filter(models.Task.assigned_to == current_user.id).all()


@router.get("/delayed", response_model=List[schemas.TaskOut])
def delayed_tasks(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    now = datetime.utcnow()
    return (
        db.query(models.Task)
        .filter(models.Task.deadline < now, models.Task.status != "completed")
        .all()
    )


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Engineer: can only update status/progress on their own tasks.
    Manager/Admin: can update any field.
    """
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role == "engineer" and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="You can only update your own tasks")

    old_status = task.status
    old_progress = task.progress

    update_data = data.dict(exclude_unset=True, exclude={"note"})
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()

    # auto-complete: if progress reaches 100, mark completed
    if task.progress >= 100 and task.status != "completed":
        task.status = "completed"
        task.progress = 100

    db.commit()
    db.refresh(task)

    # audit log
    if old_status != task.status or old_progress != task.progress:
        log = models.TaskLog(
            task_id=task.id,
            changed_by=current_user.id,
            old_status=old_status,
            new_status=task.status,
            old_progress=old_progress,
            new_progress=task.progress,
            note=data.note,
        )
        db.add(log)
        db.commit()

    return task


@router.get("/{task_id}/logs", response_model=List[schemas.TaskLogOut])
def task_logs(task_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.TaskLog).filter(models.TaskLog.task_id == task_id).all()


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"message": "Task deleted"}
