from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.meetings import router as meetings_router
from app.core.database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meeting Bundle API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(meetings_router)


@app.get("/health")
def health():
    return {"status": "ok"}
