"""
database/db.py
---------------
SQLite connection + schema management for SAGE.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    device_id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'offline',
    last_seen TEXT
);

CREATE TABLE IF NOT EXISTS sensor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    temperature REAL,
    gas REAL,
    motion INTEGER,
    flame INTEGER,
    overflow INTEGER,
    risk_score INTEGER,
    risk_level TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT,
    severity TEXT,
    temperature REAL,
    gas REAL,
    motion INTEGER,
    flame INTEGER,
    risk_score INTEGER,
    action_taken TEXT,
    status TEXT DEFAULT 'Completed',
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command TEXT,
    status TEXT,
    timestamp TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DEFAULT_SETTINGS = {
    "gas_threshold": "400",
    "temperature_threshold": "80",
    "risk_threshold": "61",
    "auto_shutoff_timeout": "10",
    "notify_telegram": "false",
    "notify_email": "false",
    "notify_browser": "true",
    "units": "C",
}


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)

    # Seed default settings if empty
    cur = conn.execute("SELECT COUNT(*) as c FROM settings")
    if cur.fetchone()["c"] == 0:
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed the ESP32 device record
    cur = conn.execute("SELECT COUNT(*) as c FROM devices")
    if cur.fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO devices (device_id, status, last_seen) VALUES (?, ?, ?)",
            ("ESP32-SAGE-01", "online", datetime.utcnow().isoformat() + "Z"),
        )

    # Seed a demo user
    cur = conn.execute("SELECT COUNT(*) as c FROM users")
    if cur.fetchone()["c"] == 0:
        conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
            ("Demo User", "demo@sage.local", "demo123"),
        )

    conn.commit()
    conn.close()


def get_settings():
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def update_settings(new_values: dict):
    conn = get_connection()
    for k, v in new_values.items():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, str(v)),
        )
    conn.commit()
    conn.close()
