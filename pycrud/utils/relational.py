from __future__ import annotations
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

def read_table_df(session: Session, table: str) -> pd.DataFrame:
    return pd.read_sql(text(f"SELECT * FROM {table}"), session.bind)

def join(session: Session, left: str, right: str, on_left: str, on_right: str, how="inner") -> pd.DataFrame:
    A = read_table_df(session, left)
    B = read_table_df(session, right)
    return A.merge(B, left_on=on_left, right_on=on_right, how=how)

def project(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df[cols].copy()

def select(df: pd.DataFrame, expr: str) -> pd.DataFrame:
    return df.query(expr)
