import sqlite3
import os

db_path = os.path.join('backend', 'word2latex.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the last job from conversions table
with open('backend/job_info.txt', 'w', encoding='utf-8') as f:
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        target_table = None
        for t in tables:
            if 'conversion' in t:
                target_table = t
                break
        
        if target_table:
            f.write(f"Target table: {target_table}\n")
            cursor.execute(f"SELECT job_id, status, file_path FROM {target_table} ORDER BY rowid DESC LIMIT 5;")
            rows = cursor.fetchall()
            for row in rows:
                f.write(f"Job ID: {row[0]}, Status: {row[1]}, Path: {row[2]}\n")
        else:
            f.write("No conversion table found.\n")
    except Exception as e:
        f.write(f"Error: {e}\n")

conn.close()
