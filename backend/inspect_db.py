import sqlite3
import os

db_path = os.path.join('backend', 'word2latex.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
print(f"Tables found: {tables}")

for table in tables:
    print(f"\nTable: {table}")
    cursor.execute(f"PRAGMA table_info({table});")
    print(f"Columns: {[c[1] for c in cursor.fetchall()]}")
    cursor.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 3;")
    for row in cursor.fetchall():
        print(row)

conn.close()
