from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, DateTime, Boolean, Text, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    meetings: Mapped[list["Meeting"]] = relationship(back_populates="owner", cascade="all, delete-orphan")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    uploaded_docx_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="meetings")
    output: Mapped["MeetingOutput"] = relationship(back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")
    emails: Mapped[list["GeneratedEmail"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class MeetingOutput(Base):
    __tablename__ = "meeting_outputs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), unique=True, nullable=False)
    crm_contact_type: Mapped[str] = mapped_column(String(30), default="existing")
    crm_company: Mapped[str] = mapped_column(String(255), default="")
    crm_contact_name: Mapped[str] = mapped_column(String(255), default="")
    crm_contact_email: Mapped[str] = mapped_column(String(255), default="")
    crm_update_notes: Mapped[str] = mapped_column(Text, default="")
    crm_follow_up_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    crm_follow_up_tasks_text: Mapped[str] = mapped_column(Text, default="")
    generated_summary: Mapped[str] = mapped_column(Text, default="")
    next_step: Mapped[str] = mapped_column(Text, default="")
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    edited_by_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting: Mapped["Meeting"] = relationship(back_populates="output")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    task_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(default=0)

    meeting: Mapped["Meeting"] = relationship(back_populates="tasks")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    template_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    subject_template: Mapped[str] = mapped_column(String(255), nullable=False)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class GeneratedEmail(Base):
    __tablename__ = "generated_emails"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id"), nullable=False)
    template_key: Mapped[str] = mapped_column(String(100), nullable=False)
    generated_subject: Mapped[str] = mapped_column(String(255), default="")
    generated_body: Mapped[str] = mapped_column(Text, default="")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    meeting: Mapped["Meeting"] = relationship(back_populates="emails")
