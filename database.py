import sqlite3
from flask import g
import config


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(config.DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(config.DATABASE)
    c = db.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            storage_limit INTEGER DEFAULT 104857600,
            failed_attempts INTEGER DEFAULT 0,
            blocked_until INTEGER DEFAULT 0
        )
    """)

    db.commit()
    db.close()
