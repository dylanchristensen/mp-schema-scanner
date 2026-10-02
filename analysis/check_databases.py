import sqlite3
import os

dbs = [
    "smart_home_composed_scope2_traces.db",
    "smart_home_composed_traces.db",
    "smart_home_traces.db",
    "smart_home_traces_scope3.db"
]

path_prefix = "data"

for db_name in dbs:
    db_path = os.path.join(path_prefix, db_name)
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM traces")
            count = cur.fetchone()[0]
            print(f"{db_name}: {count} traces")
            
            # Check what states are present
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='trace_states'")
            has_states = cur.fetchone()[0]
            if has_states:
                cur.execute("SELECT mark, COUNT(*) FROM traces GROUP BY mark")
                marks = cur.fetchall()
                print(f"  Marks: {marks}")
        except Exception as e:
            print(f"{db_name}: error {e}")
        finally:
            conn.close()
    else:
        print(f"{db_name}: NOT FOUND")
