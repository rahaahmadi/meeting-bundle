# Meeting Bundle

Web app for turning meetings into actionable bundles: transcripts, AI-generated summaries, CRM notes, tasks, and email drafts—with auth, review, and approval notifications.

## Tech stack

**Backend:** FastAPI, Uvicorn, SQLAlchemy, OpenAI Responses API, JWT (`Authorization: Bearer <token>`).

**Frontend:** React 18, React Router, Vite, Axios.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `backend/.env`, then:

```bash
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App: `http://localhost:5173`
- The client defaults to `http://localhost:8000`. Override with `VITE_API_BASE_URL` (e.g. in `frontend/.env`) before `npm run dev`.

## Backend environment variables

See `backend/.env.example`:

| Variable | Notes |
|----------|--------|
| `OPENAI_API_KEY` | Required for AI generation |
| `OPENAI_MODEL` | Defaults to `gpt-4.1-mini` |
| `OPENAI_TIMEOUT_SECONDS` | OpenAI request timeout |
| `DATABASE_URL` | Defaults to `sqlite:///./app.db` |
| `JWT_SECRET_KEY` | Change outside local dev |
| `JWT_ALGORITHM` | Defaults to `HS256` |
| `JWT_EXPIRE_MINUTES` | Access token lifetime |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_FROM` | Approval notification email |

## Workflow

1. Register or log in.
2. Create a meeting record.
3. Upload a transcript or paste meeting text.
4. Generate the bundle.
5. Review and edit outputs, tasks, and emails.
6. Approve the meeting bundle.
