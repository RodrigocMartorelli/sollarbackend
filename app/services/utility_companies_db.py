from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

DB_FILE = Path(__file__).resolve().parent / "data" / "utility_companies.db"


def _get_conn(create: bool = False) -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_FILE))
    if create:
        # ensure schema exists even if DB file already present
        _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS utility_companies (
            codigo_ibge INTEGER PRIMARY KEY,
            uf TEXT NOT NULL,
            municipio TEXT NOT NULL,
            concessionaria TEXT NOT NULL
        )
        """
    )
    # table to store distinct company names (when we can't map to municipio yet)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
        """
    )
    conn.commit()


def init_db() -> None:
    _get_conn(create=True).close()


def insert_company(codigo_ibge: int, uf: str, municipio: str, concessionaria: str) -> None:
    conn = _get_conn(create=True)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO utility_companies(codigo_ibge, uf, municipio, concessionaria) VALUES (?, ?, ?, ?)",
        (int(codigo_ibge), uf.strip().upper(), municipio.strip(), concessionaria.strip()),
    )
    conn.commit()
    conn.close()


def get_company_by_ibge(codigo_ibge: int) -> Optional[str]:
    if not DB_FILE.exists():
        return None
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT concessionaria FROM utility_companies WHERE codigo_ibge = ?", (int(codigo_ibge),))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def get_all_companies() -> list[str]:
    if not DB_FILE.exists():
        return []
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # get distinct concessionarias from utility_companies and explicit companies table
        cur.execute(
            "SELECT concessionaria as name FROM utility_companies WHERE concessionaria IS NOT NULL UNION SELECT name FROM companies ORDER BY name"
        )
    except sqlite3.OperationalError as e:
        # if companies table doesn't exist yet, ensure schema (create it) and retry once
        if "no such table" in str(e):
            conn.close()
            _get_conn(create=True).close()
            conn = _get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT concessionaria as name FROM utility_companies WHERE concessionaria IS NOT NULL UNION SELECT name FROM companies ORDER BY name"
            )
        else:
            conn.close()
            raise
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows if r and r[0]]


def insert_company_name(name: str) -> None:
    conn = _get_conn(create=True)
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO companies(name) VALUES (?)", (name.strip(),))
        conn.commit()
    finally:
        conn.close()


def import_from_csv(path: str | Path) -> int:
    import csv

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(path))
    conn = _get_conn(create=True)
    cur = conn.cursor()
    count = 0
    with p.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            try:
                codigo = int(r.get("codigo_ibge") or r.get("codigo") or 0)
                uf = (r.get("uf") or r.get("estado") or "").strip().upper()
                municipio = (r.get("municipio") or r.get("cidade") or "").strip()
                concessionaria = (r.get("concessionaria") or r.get("fornecedora") or "").strip()
                if codigo and uf and municipio and concessionaria:
                    cur.execute(
                        "INSERT OR REPLACE INTO utility_companies(codigo_ibge, uf, municipio, concessionaria) VALUES (?, ?, ?, ?)",
                        (codigo, uf, municipio, concessionaria),
                    )
                    count += 1
            except Exception:
                continue
    conn.commit()
    conn.close()
    return count
