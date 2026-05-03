from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str

    class Config:
        from_attributes = True


class MeetingCreate(BaseModel):
    title: str
    meeting_date: date


class GenerateBundleRequest(BaseModel):
    meeting_text: Optional[str] = None


class MeetingResponse(BaseModel):
    id: int
    title: str
    meeting_date: date
    status: str

    class Config:
        from_attributes = True


class TaskItem(BaseModel):
    task_text: str
    is_checked: bool = False


class CRMBlock(BaseModel):
    contact_type: Literal["new", "existing"] = "existing"
    company: str = ""
    contact_name: str = ""
    contact_email: str = ""
    recommended_services: str = ""
    update_notes: str = ""
    follow_up_date: Optional[date] = None
    follow_up_tasks: str = ""
    next_step: str = ""


class GeneratedEmailPayload(BaseModel):
    template_key: str
    subject: str
    body: str


class GenerationResult(BaseModel):
    summary: str
    crm: CRMBlock
    participant_tasks: list[TaskItem]
    my_tasks: list[TaskItem]
    emails: list[GeneratedEmailPayload]


class MeetingBundleResponse(BaseModel):
    meeting: MeetingResponse
    summary: str
    crm: CRMBlock
    participant_tasks: list[TaskItem]
    my_tasks: list[TaskItem]
    emails: list[GeneratedEmailPayload]


class UpdateOutputRequest(BaseModel):
    summary: str
    crm: CRMBlock
    participant_tasks: list[TaskItem] = []


class UpdateTasksRequest(BaseModel):
    tasks: list[TaskItem]


class UpdateEmailRequest(BaseModel):
    subject: str
    body: str
