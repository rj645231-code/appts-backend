from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum


class RoleEnum(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    engineer = "engineer"


class StatusEnum(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    delayed = "delayed"


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, default=RoleEnum.engineer)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # ── NEW: email verification ──────────────────────────
    is_email_verified = Column(Boolean, default=False)
    email_otp = Column(String, nullable=True)          # 6-digit code
    otp_expires_at = Column(DateTime, nullable=True)

    # ── NEW: admin approval ──────────────────────────────
    # pending | approved | rejected
    approval_status = Column(String, default="pending")
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")
    managed_projects = relationship("Project", back_populates="manager")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default=StatusEnum.pending)
    priority = Column(String, default=PriorityEnum.medium)
    start_date = Column(DateTime, default=datetime.utcnow)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    manager = relationship("User", back_populates="managed_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default=StatusEnum.pending)
    priority = Column(String, default=PriorityEnum.medium)
    progress = Column(Integer, default=0)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class TaskLog(Base):
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    changed_by = Column(Integer, ForeignKey("users.id"))
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=True)
    old_progress = Column(Integer, nullable=True)
    new_progress = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="logs")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    author = relationship("User")
