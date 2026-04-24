"""SQLite persistence for analysis history and manual price history."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import pandas as pd


DB_PATH = Path("anomalia_cenowa.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                threshold_pct REAL,
                n_records INTEGER,
                n_anomalies INTEGER,
                n_idx_anomalies INTEGER,
                analysis_type TEXT DEFAULT 'Auto',
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_mat TEXT,
                price REAL,
                source TEXT DEFAULT 'Ręczna',
                session_id TEXT,
                analysis_id INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.commit()


def save_analysis(
    file_name: str,
    threshold_pct: float,
    n_records: int,
    n_anomalies: int,
    n_idx_anomalies: int,
    analysis_type: str = "Auto",
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO analysis_history
               (file_name, threshold_pct, n_records, n_anomalies, n_idx_anomalies, analysis_type)
               VALUES (?,?,?,?,?,?)""",
            (file_name, threshold_pct, n_records, n_anomalies, n_idx_anomalies, analysis_type),
        )
        conn.commit()
        return cur.lastrowid


def save_price(index_mat: str, price: float, session_id: str, analysis_id: Optional[int] = None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO price_history (index_mat, price, session_id, analysis_id)
               VALUES (?,?,?,?)""",
            (index_mat, price, session_id, analysis_id),
        )
        conn.commit()


def get_last_price(index_mat: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT price, created_at FROM price_history WHERE index_mat=? ORDER BY id DESC LIMIT 1",
            (index_mat,),
        ).fetchone()
        if row:
            return {"price": row["price"], "created_at": row["created_at"]}
    return None


def get_analysis_history() -> pd.DataFrame:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, file_name, threshold_pct, n_records, n_anomalies, n_idx_anomalies, analysis_type, created_at FROM analysis_history ORDER BY id DESC"
        ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["ID", "Plik", "Próg %", "Rekordy", "Anomalie", "Indeksy z anom.", "Typ", "Data"])
    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=["id", "file_name", "threshold_pct", "n_records", "n_anomalies", "n_idx_anomalies", "analysis_type", "created_at"],
    ).rename(columns={
        "id": "ID", "file_name": "Plik", "threshold_pct": "Próg %",
        "n_records": "Rekordy", "n_anomalies": "Anomalie",
        "n_idx_anomalies": "Indeksy z anom.", "analysis_type": "Typ", "created_at": "Data",
    })


def get_price_history() -> pd.DataFrame:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, index_mat, price, source, session_id, analysis_id, created_at FROM price_history ORDER BY id DESC"
        ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["ID", "Index materiałowy", "Cena", "Źródło", "Sesja", "ID analizy", "Data"])
    return pd.DataFrame(
        [dict(r) for r in rows],
    ).rename(columns={
        "id": "ID", "index_mat": "Index materiałowy", "price": "Cena",
        "source": "Źródło", "session_id": "Sesja", "analysis_id": "ID analizy", "created_at": "Data",
    })
