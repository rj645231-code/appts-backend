from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from auth import get_current_user, require_role
import models, schemas
from datetime import datetime
from typing import List

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=schemas.ProjectOut)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    new_project = models.Project(
        project_name=project.project_name,
        description=project.description,
        manager_id=current_user.id,
        priority=project.priority,
        deadline=project.deadline,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@router.get("/", response_model=List[schemas.ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.Project).all()


@router.get("/summary", response_model=schemas.OverallSummary)
def overall_summary(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Manager/Admin: global KPIs across all projects."""
    total_projects = db.query(func.count(models.Project.id)).scalar()
    total_tasks = db.query(func.count(models.Task.id)).scalar()
    completed = db.query(func.count(models.Task.id)).filter(models.Task.status == "completed").scalar()
    in_progress = db.query(func.count(models.Task.id)).filter(models.Task.status == "in_progress").scalar()
    pending = db.query(func.count(models.Task.id)).filter(models.Task.status == "pending").scalar()

    now = datetime.utcnow()
    delayed = db.query(func.count(models.Task.id)).filter(
        models.Task.deadline < now,
        models.Task.status != "completed",
    ).scalar()

    avg_progress = db.query(func.avg(models.Task.progress)).scalar() or 0.0

    return {
        "total_projects": total_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "pending_tasks": pending,
        "delayed_tasks": delayed,
        "overall_progress": round(float(avg_progress), 1),
    }


@router.get("/workload", response_model=List[schemas.WorkloadItem])
def workload_analysis(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Per-engineer workload breakdown."""
    engineers = db.query(models.User).filter(models.User.role == "engineer").all()
    result = []
    for eng in engineers:
        tasks = db.query(models.Task).filter(models.Task.assigned_to == eng.id).all()
        completed = sum(1 for t in tasks if t.status == "completed")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        pending = sum(1 for t in tasks if t.status == "pending")
        avg_prog = sum(t.progress for t in tasks) / len(tasks) if tasks else 0
        result.append({
            "user_id": eng.id,
            "name": eng.name,
            "total_tasks": len(tasks),
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "avg_progress": round(avg_prog, 1),
        })
    return result


@router.get("/dashboard/{project_id}", response_model=schemas.ProjectDashboard)
def project_dashboard(project_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == "completed")
    in_progress = sum(1 for t in tasks if t.status == "in_progress")

    now = datetime.utcnow()
    delayed = sum(1 for t in tasks if t.deadline and t.deadline < now and t.status != "completed")
    progress = round(sum(t.progress for t in tasks) / total, 1) if total else 0.0
    is_overdue = bool(project.deadline and project.deadline < now and project.status != "completed")

    return {
        "project_name": project.project_name,
        "status": project.status,
        "priority": project.priority,
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "delayed_tasks": delayed,
        "project_progress": progress,
        "deadline": project.deadline,
        "is_overdue": is_overdue,
    }


@router.patch("/{project_id}", response_model=schemas.ProjectOut)
def update_project(
    project_id: int,
    data: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}
