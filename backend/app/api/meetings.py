import os
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.models import User, Meeting, MeetingOutput, Task, GeneratedEmail
from app.schemas.schemas import (
    MeetingCreate,
    GenerateBundleRequest,
    MeetingResponse,
    MeetingBundleResponse,
    TaskItem,
    CRMBlock,
    GeneratedEmailPayload,
    UpdateOutputRequest,
    UpdateTasksRequest,
    UpdateEmailRequest,
)
from app.services.email_service import send_owner_notification
from app.services.openai_service import OpenAIService
from app.utils.docx_parser import extract_text_from_docx


router = APIRouter(prefix="/meetings", tags=["meetings"])
openai_service = OpenAIService()
RECOMMENDED_SERVICES_HEADER = "Recommended Services/Packages:"
FILE_LINK_MAP = {
    "Less Annoying CRM": "www.lessannoyingcrm.com/invite/12357F",
}
ISO_DATE_PATTERN = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")


def _tasks_to_text(tasks: list[TaskItem]) -> str:
    return "\n".join([f"- {t.task_text}" for t in tasks if t.task_text.strip()])


def _text_to_tasks(task_text: str) -> list[TaskItem]:
    tasks: list[TaskItem] = []
    for line in task_text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        if clean.startswith("- "):
            clean = clean[2:].strip()
        tasks.append(TaskItem(task_text=clean, is_checked=False))
    return tasks


def _split_crm_notes(raw_notes: str) -> tuple[str, str]:
    notes = (raw_notes or "").strip()
    if not notes.startswith(RECOMMENDED_SERVICES_HEADER):
        return "", notes

    body = notes[len(RECOMMENDED_SERVICES_HEADER):].strip()
    if "\n\n" in body:
        recommended, remainder = body.split("\n\n", 1)
        return recommended.strip(), remainder.strip()
    return body.strip(), ""


def _merge_crm_notes(recommended_services: str, update_notes: str) -> str:
    recommended = (recommended_services or "").strip()
    notes = (update_notes or "").strip()
    if not recommended:
        return notes
    if not notes:
        return f"{RECOMMENDED_SERVICES_HEADER}\n{recommended}"
    return f"{RECOMMENDED_SERVICES_HEADER}\n{recommended}\n\n{notes}"


def _replace_file_names_with_links(text: str) -> str:
    updated = text or ""
    for key, link in FILE_LINK_MAP.items():
        normalized_link = link if link.startswith(("http://", "https://")) else f"https://{link}"
        updated = updated.replace(key, f"{key}: {normalized_link}")
    return updated


def _format_iso_dates_in_text(text: str) -> str:
    raw = text or ""

    def replace(match: re.Match) -> str:
        year, month, day = match.groups()
        try:
            parsed = datetime(int(year), int(month), int(day))
        except ValueError:
            return match.group(0)
        return f"{parsed.strftime('%B')} {parsed.day}"

    return ISO_DATE_PATTERN.sub(replace, raw)


def _normalize_output_text(text: str) -> str:
    return _format_iso_dates_in_text(_replace_file_names_with_links(text))


def _get_meeting_or_404(db: Session, meeting_id: int, user_id: int) -> Meeting:
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id, Meeting.owner_user_id == user_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


def _bundle_response(meeting: Meeting) -> MeetingBundleResponse:
    output = meeting.output
    my_tasks = [TaskItem(task_text=t.task_text, is_checked=t.is_checked) for t in sorted(meeting.tasks, key=lambda x: x.sort_order)]
    participant_tasks = _text_to_tasks(output.crm_follow_up_tasks_text)
    recommended_services, update_notes = _split_crm_notes(output.crm_update_notes)
    emails = [
        GeneratedEmailPayload(template_key=e.template_key, subject=e.generated_subject, body=e.generated_body)
        for e in meeting.emails
    ]
    crm = CRMBlock(
        contact_type=output.crm_contact_type,
        company=output.crm_company,
        contact_name=output.crm_contact_name,
        contact_email=output.crm_contact_email,
        recommended_services=recommended_services,
        update_notes=update_notes,
        follow_up_date=output.crm_follow_up_date,
        follow_up_tasks=output.crm_follow_up_tasks_text,
        next_step=output.next_step,
    )
    return MeetingBundleResponse(
        meeting=MeetingResponse.model_validate(meeting),
        summary=output.generated_summary,
        crm=crm,
        participant_tasks=participant_tasks,
        my_tasks=my_tasks,
        emails=emails,
    )


@router.post("", response_model=MeetingResponse)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = Meeting(owner_user_id=current_user.id, title=payload.title, meeting_date=payload.meeting_date, status="uploaded")
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=list[MeetingResponse])
def list_meetings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Meeting).filter(Meeting.owner_user_id == current_user.id).order_by(Meeting.created_at.desc()).all()


@router.post("/{meeting_id}/upload-docx")
def upload_docx(meeting_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files supported")

    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{meeting_id}-{datetime.utcnow().timestamp()}.docx"

    with file_path.open("wb") as buffer:
        buffer.write(file.file.read())

    meeting.uploaded_docx_path = str(file_path)
    meeting.status = "uploaded"
    db.commit()

    return {"message": "File uploaded"}


@router.post("/{meeting_id}/generate-bundle", response_model=MeetingBundleResponse)
def generate_bundle(
    meeting_id: int,
    payload: GenerateBundleRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    pasted_text = (payload.meeting_text or "").strip() if payload else ""
    if pasted_text:
        meeting_text = pasted_text
    elif meeting.uploaded_docx_path and os.path.exists(meeting.uploaded_docx_path):
        meeting_text = extract_text_from_docx(meeting.uploaded_docx_path)
    else:
        raise HTTPException(status_code=400, detail="Upload .docx or paste meeting text first")
    try:
        result = openai_service.generate_bundle(meeting_text)
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to generate structured bundle: {exc}")

    result.summary = _normalize_output_text(result.summary)
    result.crm.recommended_services = _normalize_output_text(result.crm.recommended_services)
    result.crm.update_notes = _normalize_output_text(result.crm.update_notes)
    result.crm.next_step = _normalize_output_text(result.crm.next_step)
    for task in result.participant_tasks:
        task.task_text = _normalize_output_text(task.task_text)
    for task in result.my_tasks:
        task.task_text = _normalize_output_text(task.task_text)
    for email in result.emails:
        email.subject = _normalize_output_text(email.subject)
        email.body = _normalize_output_text(email.body)

    if not meeting.output:
        meeting.output = MeetingOutput(meeting_id=meeting.id)

    meeting.output.crm_contact_type = result.crm.contact_type
    meeting.output.crm_company = result.crm.company
    meeting.output.crm_contact_name = result.crm.contact_name
    meeting.output.crm_contact_email = result.crm.contact_email
    meeting.output.crm_update_notes = _merge_crm_notes(result.crm.recommended_services, result.crm.update_notes)
    meeting.output.crm_follow_up_date = result.crm.follow_up_date
    meeting.output.generated_summary = result.summary
    meeting.output.next_step = result.crm.next_step

    db.query(Task).filter(Task.meeting_id == meeting.id).delete()
    for i, t in enumerate(result.my_tasks):
        db.add(Task(meeting_id=meeting.id, task_text=t.task_text, is_checked=t.is_checked, sort_order=i))
    meeting.output.crm_follow_up_tasks_text = _tasks_to_text(result.participant_tasks)

    db.query(GeneratedEmail).filter(GeneratedEmail.meeting_id == meeting.id).delete()
    for email in result.emails:
        db.add(
            GeneratedEmail(
                meeting_id=meeting.id,
                template_key=email.template_key,
                generated_subject=email.subject,
                generated_body=email.body,
            )
        )

    meeting.status = "generated"
    db.commit()
    db.refresh(meeting)
    return _bundle_response(meeting)


@router.get("/{meeting_id}", response_model=MeetingBundleResponse)
def get_meeting(meeting_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    if not meeting.output:
        raise HTTPException(status_code=400, detail="Bundle not generated yet")
    return _bundle_response(meeting)


@router.patch("/{meeting_id}/outputs", response_model=MeetingBundleResponse)
def update_outputs(meeting_id: int, payload: UpdateOutputRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    if not meeting.output:
        meeting.output = MeetingOutput(meeting_id=meeting.id)

    meeting.output.generated_summary = payload.summary
    meeting.output.crm_contact_type = payload.crm.contact_type
    meeting.output.crm_company = payload.crm.company
    meeting.output.crm_contact_name = payload.crm.contact_name
    meeting.output.crm_contact_email = payload.crm.contact_email
    meeting.output.crm_update_notes = _merge_crm_notes(payload.crm.recommended_services, payload.crm.update_notes)
    meeting.output.crm_follow_up_date = payload.crm.follow_up_date
    meeting.output.crm_follow_up_tasks_text = _tasks_to_text(payload.participant_tasks)
    meeting.output.next_step = payload.crm.next_step
    meeting.output.edited_by_user = True

    db.commit()
    db.refresh(meeting)
    return _bundle_response(meeting)


@router.put("/{meeting_id}/tasks", response_model=MeetingBundleResponse)
def update_tasks(meeting_id: int, payload: UpdateTasksRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    db.query(Task).filter(Task.meeting_id == meeting.id).delete()

    task_lines = []
    for i, t in enumerate(payload.tasks):
        db.add(Task(meeting_id=meeting.id, task_text=t.task_text, is_checked=t.is_checked, sort_order=i))
        task_lines.append(f"- {t.task_text}")

    db.commit()
    db.refresh(meeting)
    return _bundle_response(meeting)


@router.patch("/{meeting_id}/emails/{template_key}", response_model=MeetingBundleResponse)
def update_email(meeting_id: int, template_key: str, payload: UpdateEmailRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    email = (
        db.query(GeneratedEmail)
        .filter(GeneratedEmail.meeting_id == meeting.id, GeneratedEmail.template_key == template_key)
        .first()
    )
    if not email:
        raise HTTPException(status_code=404, detail="Email template output not found")

    email.generated_subject = payload.subject
    email.generated_body = payload.body
    db.commit()
    db.refresh(meeting)
    return _bundle_response(meeting)


@router.post("/{meeting_id}/approve", response_model=MeetingBundleResponse)
def approve(meeting_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    meeting = _get_meeting_or_404(db, meeting_id, current_user.id)
    if not meeting.output:
        raise HTTPException(status_code=400, detail="Generate bundle first")

    meeting.output.approved_at = datetime.utcnow()
    meeting.status = "approved"
    db.commit()
    db.refresh(meeting)

    try:
        send_owner_notification(current_user.email, meeting.title)
    except Exception:
        pass

    return _bundle_response(meeting)
