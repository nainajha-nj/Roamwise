import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import httpx

BASE_DIR = Path(__file__).resolve().parents[1]

def _db_path():
    raw = os.getenv("DATABASE_PATH", "roamwise.db")
    p = Path(raw)
    return p if p.is_absolute() else BASE_DIR / p

def _use_supabase():
    return bool(os.getenv("SUPABASE_URL", "").strip() and os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip())

def _headers():
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=representation"}

def init_store():
    if _use_supabase(): return
    with sqlite3.connect(_db_path()) as con:
        con.execute("CREATE TABLE IF NOT EXISTS trips (id TEXT PRIMARY KEY, title TEXT NOT NULL, destination TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL)")
        con.commit()

def list_trips():
    if _use_supabase():
        r = httpx.get(os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/trips?select=id,title,destination,created_at,payload&order=created_at.desc', headers=_headers(), timeout=12); r.raise_for_status()
        return [x['payload'] for x in r.json()]
    init_store()
    with sqlite3.connect(_db_path()) as con:
        rows = con.execute("SELECT payload FROM trips ORDER BY created_at DESC").fetchall()
    return [json.loads(r[0]) for r in rows]

def get_trip(trip_id):
    if _use_supabase():
        r = httpx.get(os.environ['SUPABASE_URL'].rstrip('/') + f'/rest/v1/trips?id=eq.{trip_id}&select=payload', headers=_headers(), timeout=12); r.raise_for_status()
        rows = r.json(); return rows[0]['payload'] if rows else None
    init_store()
    with sqlite3.connect(_db_path()) as con:
        row = con.execute("SELECT payload FROM trips WHERE id=?", (trip_id,)).fetchone()
    return json.loads(row[0]) if row else None

def save_trip(payload):
    data = dict(payload); data['id'] = data.get('id') or str(uuid4()); data['created_at'] = data.get('created_at') or datetime.now(timezone.utc).isoformat()
    if _use_supabase():
        row = {"id": data['id'], "title": data['title'], "destination": data['destination'], "created_at": data['created_at'], "payload": data}
        r = httpx.post(os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/trips', headers=_headers(), json=row, timeout=12); r.raise_for_status()
        return data
    init_store()
    with sqlite3.connect(_db_path()) as con:
        con.execute("INSERT OR REPLACE INTO trips(id,title,destination,created_at,payload) VALUES(?,?,?,?,?)", (data['id'], data['title'], data['destination'], data['created_at'], json.dumps(data)))
        con.commit()
    return data

def delete_trip(trip_id):
    if _use_supabase():
        r = httpx.delete(os.environ['SUPABASE_URL'].rstrip('/') + f'/rest/v1/trips?id=eq.{trip_id}', headers=_headers(), timeout=12); r.raise_for_status(); return r.status_code in (200,204)
    init_store()
    with sqlite3.connect(_db_path()) as con:
        cur = con.execute("DELETE FROM trips WHERE id=?", (trip_id,)); con.commit(); return cur.rowcount > 0
