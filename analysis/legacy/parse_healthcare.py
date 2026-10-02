import json
import sqlite3
import os

DB_FILE = "data/healthcare_traces.db"
GRY_CONSTRAINED = "data/healthcareDelivery_scope_1.gry"
GRY_UNCONSTRAINED = "data/healthcareDelivery_scope_2.gry"

COMPONENTS = ["Patient", "Clinical Device", "EHR System", "Physician", "Pharmacy", "Insurance"]
COL_NAMES = {
    "Patient": "patient",
    "Clinical Device": "clinical_device",
    "EHR System": "ehr_system",
    "Physician": "physician",
    "Pharmacy": "pharmacy",
    "Insurance": "insurance"
}

def parse_gry_to_db(gry_path, suffix, conn):
    print(f"Parsing {gry_path}...")
    with open(gry_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    graphs = data.get("graphs", [])
    print(f"Total entries: {len(graphs)}")
    
    cur = conn.cursor()
    
    # Create tables
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS traces_{suffix} (
            trace_id INTEGER PRIMARY KEY,
            mark TEXT
        )
    """)
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS trace_states_{suffix} (
            trace_id INTEGER PRIMARY KEY,
            patient TEXT,
            clinical_device TEXT,
            ehr_system TEXT,
            physician TEXT,
            pharmacy TEXT,
            insurance TEXT,
            FOREIGN KEY(trace_id) REFERENCES traces_{suffix}(trace_id)
        )
    """)
    
    bt, bs = [], []
    trace_idx = 0
    
    for g in graphs:
        trace = g.get("trace")
        if trace is None:
            continue
            
        trace_idx += 1
        mark = trace.get("mark", "")
        nodes = trace.get("nodes", [])
        edges = trace.get("edges", [])
        
        # parent mapping
        parent_map = {}
        for edge in edges:
            if edge.get("relation") == "IN":
                parent_map[edge["to_id"]] = edge["from_id"]
                
        node_map = {n["id"]: n for n in nodes}
        states = {}
        
        for node in nodes:
            if node["type"] == "C":
                pid = parent_map.get(node["id"])
                if pid and pid in node_map:
                    root_label = node_map[pid]["label"]
                    if root_label in COL_NAMES:
                        states[COL_NAMES[root_label]] = node["label"]
                        
        bt.append((trace_idx, mark))
        bs.append((
            trace_idx,
            states.get("patient", ""),
            states.get("clinical_device", ""),
            states.get("ehr_system", ""),
            states.get("physician", ""),
            states.get("pharmacy", ""),
            states.get("insurance", "")
        ))
        
        if trace_idx % 2000 == 0:
            cur.executemany(f"INSERT INTO traces_{suffix} VALUES (?,?)", bt)
            cur.executemany(f"INSERT INTO trace_states_{suffix} VALUES (?,?,?,?,?,?,?)", bs)
            bt.clear()
            bs.clear()
            
    cur.executemany(f"INSERT INTO traces_{suffix} VALUES (?,?)", bt)
    cur.executemany(f"INSERT INTO trace_states_{suffix} VALUES (?,?,?,?,?,?,?)", bs)
    
    # create indexes
    for col in COL_NAMES.values():
        cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{suffix}_{col} ON trace_states_{suffix}({col})")
        
    conn.commit()
    print(f"Parsed {trace_idx} traces into table trace_states_{suffix}")
    return trace_idx

def main():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        
    conn = sqlite3.connect(DB_FILE)
    
    # WAL mode for speed
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    n_const = parse_gry_to_db(GRY_CONSTRAINED, "constrained", conn)
    n_unconst = parse_gry_to_db(GRY_UNCONSTRAINED, "unconstrained", conn)
    
    print("\nState distributions in Constrained:")
    cur = conn.cursor()
    for col in COL_NAMES.values():
        print(f"\n  {col}:")
        cur.execute(f"SELECT {col}, COUNT(*) as cnt FROM trace_states_constrained GROUP BY {col} ORDER BY cnt DESC")
        for r in cur.fetchall():
            print(f"    {r[0]}: {r[1]} ({r[1]/n_const:.1%})")
            
    print("\nState distributions in Unconstrained:")
    for col in COL_NAMES.values():
        print(f"\n  {col}:")
        cur.execute(f"SELECT {col}, COUNT(*) as cnt FROM trace_states_unconstrained GROUP BY {col} ORDER BY cnt DESC")
        for r in cur.fetchall():
            print(f"    {r[0]}: {r[1]} ({r[1]/n_unconst:.1%})")
            
    conn.close()
    print(f"\nFinished parsing. Database size: {os.path.getsize(DB_FILE) / 1e6:.2f} MB")

if __name__ == "__main__":
    main()
