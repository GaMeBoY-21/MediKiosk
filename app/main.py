# Owner: Tharun
"""FastAPI application entrypoint: app instance, CORS, router registration, /health."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import session, interview, documents, summary, physician

app = FastAPI(title="MediKiosk")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(interview.router)
app.include_router(documents.router)
app.include_router(summary.router)
app.include_router(physician.router)


@app.get("/health")
def health():
    return {"status": "ok"}
