from __future__ import annotations
import tkinter as tk
from tkinter import simpledialog, messagebox
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from . import sample_data

DEFAULT_URL = "sqlite:///data/demo.sqlite"

class EngineBundle:
    def __init__(self, url: str = DEFAULT_URL):
        self.url = url
        self.engine = create_engine(self.url, future=True)
        self.SessionLocal = sessionmaker(self.engine, expire_on_commit=False, future=True)

    def create_all_and_seed(self) -> None:
        Base.metadata.create_all(self.engine)
        with self.SessionLocal() as s:
            sample_data.seed(s)

    def session(self) -> Session:
        return self.SessionLocal()

def connect_dialog(parent: tk.Tk, current_url: str = DEFAULT_URL) -> str | None:
    tip = ("Enter a SQLAlchemy URL. Examples:\n"
           "  sqlite:///data/demo.sqlite\n"
           "  mysql+pymysql://user:pass@localhost:3306/school\n"
           "  mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost;DATABASE=school;Trusted_Connection=yes;TrustServerCertificate=yes")
    dlg = tk.Toplevel(parent)
    dlg.title("Connect…")
    dlg.grab_set()
    tk.Label(dlg, text=tip, justify="left").pack(padx=10, pady=8)
    url_var = tk.StringVar(value=current_url)
    e = tk.Entry(dlg, width=100, textvariable=url_var)
    e.pack(padx=10, pady=8)
    e.focus_set()

    out = {"url": None}
    def ok():
        out["url"] = url_var.get().strip()
        dlg.destroy()
    def cancel():
        dlg.destroy()

    f = tk.Frame(dlg)
    f.pack(pady=8)
    tk.Button(f, text="OK", command=ok).pack(side="left", padx=5)
    tk.Button(f, text="Cancel", command=cancel).pack(side="left", padx=5)
    parent.wait_window(dlg)
    return out["url"]
