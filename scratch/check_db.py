import sqlite3
import os

db_path = "backend/word2latex.db"
if not os.path.exists(db_path):
    print("Database not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(payments)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Columns in payments: {columns}")
    if "plan_key" in columns:
        print("plan_key EXISTS")
    else:
        print("plan_key MISSING")
    conn.close()
