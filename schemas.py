from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── USER ────────────────────────────────────────────────
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "engineer"
    department: Optional[str] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    department: Optional[str]
    created_at: datetime
    is_email_verified: bool
    approval_status: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class ResendOTPRequest(BaseModel):
    email: EmailStr


# ── PROJECT ─────────────────────────────────────────────
class ProjectCreate(BaseModel):
    project_name: str
    description: Optional[str] = None
    priority: str = "medium"
    deadline: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    deadline: Optional[datetime] = None


class ProjectOut(BaseModel):
    id: int
    project_name: str
    description: Optional[str]
    manager_id: int
    status: str
    priority: str
    start_date: datetime
    deadline: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDashboard(BaseModel):
    project_name: str
    status: str
    priority: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    delayed_tasks: int
    project_progress: float
    deadline: Optional[datetime]
    is_overdue: bool


# ── TASK ────────────────────────────────────────────────
class TaskCreate(BaseModel):
    task_name: str
    description: Optional[str] = None
    project_id: int
    assigned_to: Optional[int] = None
    priority: str = "medium"
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    priority: Optional[str] = None
    deadline: Optional[datetime] = None
    note: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    task_name: str
    description: Optional[str]
    project_id: int
    assigned_to: Optional[int]
    status: str
    priority: str
    progress: int
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskLogOut(BaseModel):
    id: int
    task_id: int
    changed_by: int
    old_status: Optional[str]
    new_status: Optional[str]
    old_progress: Optional[int]
    new_progress: Optional[int]
    note: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True


# ── COMMENTS ────────────────────────────────────────────
class CommentCreate(BaseModel):
    message: str


class CommentOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    author_name: str
    author_role: str
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── ANALYTICS ───────────────────────────────────────────
class WorkloadItem(BaseModel):
    user_id: int
    name: str
    total_tasks: int
    completed: int
    in_progress: int
    pending: int
    avg_progress: float


class OverallSummary(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    delayed_tasks: int
    overall_progress: float
