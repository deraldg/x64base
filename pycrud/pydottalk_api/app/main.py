from __future__ import annotations
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .core.config import DB_URL, SCHEMA_PATH, FIXTURES_PATH
from .db.engine import make_engine, make_session_factory
from .api.routes import router as api_router

app = FastAPI(title="pydottalk_api", version="0.1.0")

# CORS (adjust as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine/Session
_engine = make_engine(DB_URL)
_SessionFactory = make_session_factory(_engine)

def get_session():
    with _SessionFactory() as s:
        yield s

# Dependency injection for SqlAlchemy Session and file paths
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = _SessionFactory()
    try:
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

def session_dep(request: Request) -> Session:
    return request.state.db

# Include router with dependencies and default query args for file paths
app.include_router(
    api_router,
)

# Root redirect
@app.get("/")
def root():
    return {"name": "pydottalk_api", "ok": True}
