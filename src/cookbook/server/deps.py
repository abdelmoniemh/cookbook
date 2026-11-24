"""Request dependencies: one SQLite connection per request."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

from fastapi import Request

from .. import db as dbmod


def data_dir(request: Request) -> Path:
    return request.app.state.data_dir


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = dbmod.open_db(request.app.state.data_dir, check_same_thread=False)
    try:
        yield conn
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
