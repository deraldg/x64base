from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models  # noqa: F401 (ensures models registry is imported)

def make_engine(url: str):
    eng = create_engine(url, future=True)
    return eng

def make_session_factory(eng):
    return sessionmaker(eng, expire_on_commit=False, future=True)
