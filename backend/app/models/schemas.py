from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums
class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ClusterStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"


class ServiceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


# Statistics
class DashboardStats(BaseModel):
    total_notebooks: int
    total_jobs: int
    active_clusters: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int


class JobTrends(BaseModel):
    labels: List[str]
    completed: List[int]
    failed: List[int]


# Notebooks
class NotebookCell(BaseModel):
    id: str
    cell_type: str = "code"
    source: str
    outputs: Optional[List[Dict[str, Any]]] = []
    execution_count: Optional[int] = None


class NotebookCreate(BaseModel):
    name: str
    description: Optional[str] = None


class NotebookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cells: Optional[List[NotebookCell]] = None


class Notebook(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    cells: List[NotebookCell] = []
    created_at: datetime
    updated_at: datetime
    path: Optional[str] = None


class CellExecuteRequest(BaseModel):
    code: str


class CellExecuteResponse(BaseModel):
    output: str
    execution_time: float
    status: str
    job_id: Optional[str] = None


# Jobs
class JobCreate(BaseModel):
    name: str
    code: str
    cluster_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}


class Job(BaseModel):
    id: str
    name: str
    status: JobStatus
    cluster: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[str] = None
    error_message: Optional[str] = None
    spark_ui_url: Optional[str] = None


class JobDetails(Job):
    code: Optional[str] = None
    logs: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}


class JobFilter(BaseModel):
    status: Optional[JobStatus] = None
    cluster: Optional[str] = None
    search: Optional[str] = None


# Clusters
class ClusterCreate(BaseModel):
    name: str
    worker_nodes: int = 2
    cores_per_node: int = 2
    memory_per_node: str = "2g"
    config: Optional[Dict[str, Any]] = {}


class Cluster(BaseModel):
    id: str
    name: str
    status: ClusterStatus
    master_url: str
    ui_url: str
    worker_nodes: int
    total_cores: int
    total_memory: str
    created_at: datetime


# Monitoring
class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_in: float
    network_out: float


class ServiceHealth(BaseModel):
    name: str
    status: ServiceStatus
    uptime: Optional[str] = None
    health_check: Optional[str] = None
    url: Optional[str] = None


class ServiceLog(BaseModel):
    timestamp: datetime
    level: str
    message: str


# Airflow
class DAGInfo(BaseModel):
    dag_id: str
    description: Optional[str] = None
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None


# Response models
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# Authentication & Users
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class User(UserBase):
    id: str
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[str] = None  # subject (user_id)
    exp: Optional[int] = None  # expiration time


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
