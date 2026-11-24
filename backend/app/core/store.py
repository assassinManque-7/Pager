import sqlite3, json, os
from pathlib import Path
DB_PATH = Path(os.getenv("PAGER_DB_PATH", "pager_demo.db"))
class Store:
    def __init__(self): self.db = DB_PATH
    def connect(self):
        c=sqlite3.connect(self.db); c.row_factory=sqlite3.Row; return c
    def initialize(self):
        with self.connect() as c:
            c.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT CURRENT_TIMESTAMP, incident_id TEXT, actor TEXT, event TEXT, detail TEXT)")
            c.execute("CREATE TABLE IF NOT EXISTS incidents (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    def log(self, incident_id, actor, event, detail):
        self.initialize()
        with self.connect() as c: c.execute("INSERT INTO audit(incident_id,actor,event,detail) VALUES(?,?,?,?)",(incident_id,actor,event,json.dumps(detail)))
    def audit(self):
        self.initialize()
        with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 250")]
store=Store()
