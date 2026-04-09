# store.py
import sqlite3, os, time
DB_PATH = "agent.db"

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS seen (
            message_id TEXT PRIMARY KEY,
            seen_at INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS pending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            title TEXT,
            start_iso TEXT,
            end_iso TEXT,
            location TEXT,
            online_link TEXT
        )""")

def seen_before(message_id: str) -> bool:
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT 1 FROM seen WHERE message_id=?", (message_id,))
        return cur.fetchone() is not None

def mark_seen(message_id: str):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT OR IGNORE INTO seen(message_id, seen_at) VALUES (?,?)",
                  (message_id, int(time.time())))

def add_pending(m):
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("""INSERT INTO pending(message_id,title,start_iso,end_iso,location,online_link)
                           VALUES (?,?,?,?,?,?)""",
                        (m["message_id"], m["title"], m["start_iso"], m["end_iso"], m["location"], m["online_link"]))
        return cur.lastrowid

def get_pending_by_phrase(phrase: str):
    # match numeric id in user's reply like "approve 17"
    pid = None
    try:
        pid = int(phrase.strip().split()[-1])
    except: return None
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id,message_id,title,start_iso,end_iso,location,online_link FROM pending WHERE id=?", (pid,))
        row = cur.fetchone()
        if not row: return None
        k = ["id","message_id","title","start_iso","end_iso","location","online_link"]
        return dict(zip(k,row))

def delete_pending(pid: int):
    with sqlite3.connect(DB_PATH) as c:
        c.execute("DELETE FROM pending WHERE id=?", (pid,))