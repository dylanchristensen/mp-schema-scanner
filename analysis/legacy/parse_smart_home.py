"""
Parse Smart_Home_Energy_Composed constrained.gry into a 7-column trace DB.
Follows the same pattern as parse_healthcare.py.
"""
import json
import sqlite3
import os

DB_FILE = "data/smart_home_constrained_traces.db"
GRY = "data/constrained.gry"

# .gry root labels (have spaces, not underscores)
COL_NAMES = {
    "Solar Inverter":  "solar_inverter",
    "EV System":       "ev_system",
    "Home Battery":    "home_battery",
    "HEMS":            "hems",
    "Grid Connection": "grid_connection",
    "Thermal Loads":   "thermal_loads",
    "Comm Gateway":    "comm_gateway",
}


def parse_gry_to_db(gry_path, suffix, conn):
    print(f"Loading {gry_path}...")
    with open(gry_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    graphs = data.get("graphs", [])
    print(f"Total entries: {len(graphs)}")

    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS traces_{suffix} (
            trace_id INTEGER PRIMARY KEY,
            mark TEXT
        )
    """)
    cols_def = ",\n            ".join(f"{c} TEXT" for c in COL_NAMES.values())
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS trace_states_{suffix} (
            trace_id INTEGER PRIMARY KEY,
            {cols_def},
            FOREIGN KEY(trace_id) REFERENCES traces_{suffix}(trace_id)
        )
    """)

    bt, bs = [], []
    trace_idx = 0
    placeholders = ",".join("?" * (len(COL_NAMES) + 1))

    for g in graphs:
        trace = g.get("trace")
        if trace is None:
            continue
        trace_idx += 1
        mark = trace.get("mark", "")
        nodes = trace.get("nodes", [])
        edges = trace.get("edges", [])

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
        bs.append((trace_idx,) + tuple(states.get(c, "") for c in COL_NAMES.values()))

        if trace_idx % 5000 == 0:
            cur.executemany(f"INSERT INTO traces_{suffix} VALUES (?,?)", bt)
            cur.executemany(
                f"INSERT INTO trace_states_{suffix} VALUES ({placeholders})", bs)
            bt.clear()
            bs.clear()
            print(f"  parsed {trace_idx}...")

    cur.executemany(f"INSERT INTO traces_{suffix} VALUES (?,?)", bt)
    cur.executemany(
        f"INSERT INTO trace_states_{suffix} VALUES ({placeholders})", bs)

    for col in COL_NAMES.values():
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{suffix}_{col} "
            f"ON trace_states_{suffix}({col})")
    conn.commit()
    print(f"Parsed {trace_idx} traces into trace_states_{suffix}.")
    return trace_idx


def main():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")

    n = parse_gry_to_db(GRY, "constrained", conn)

    print("\nState distributions (constrained):")
    cur = conn.cursor()
    for col in COL_NAMES.values():
        print(f"\n  {col}:")
        cur.execute(
            f"SELECT {col}, COUNT(*) as cnt FROM trace_states_constrained "
            f"GROUP BY {col} ORDER BY cnt DESC")
        for r in cur.fetchall():
            print(f"    {r[0]}: {r[1]} ({r[1] / n:.1%})")

    conn.close()
    print(f"\nDB size: {os.path.getsize(DB_FILE) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
