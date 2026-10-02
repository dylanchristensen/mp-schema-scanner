import json, sqlite3, os, sys, time
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from schema_parser import parse_schema

mp_path, gry_path, db_path = sys.argv[1], sys.argv[2], sys.argv[3]
schema = parse_schema(mp_path)
# root name (underscores) -> (gry_label spaces, db column)
roots = list(schema.roots.keys())
gry_to_col = {r.replace("_", " "): r.lower() for r in roots}
cols = [r.lower() for r in roots]
print(f"roots ({len(roots)}): {cols}", flush=True)

if os.path.exists(db_path): os.remove(db_path)
conn = sqlite3.connect(db_path); conn.execute("PRAGMA journal_mode=MEMORY"); conn.execute("PRAGMA synchronous=OFF")
cur = conn.cursor()
cur.execute(f"CREATE TABLE trace_states_constrained (trace_id INTEGER PRIMARY KEY, " +
            ", ".join(f"{c} TEXT" for c in cols) + ")")
ph = ",".join("?"*(len(cols)+1))

t0=time.time()
print(f"reading {os.path.getsize(gry_path)/1e6:.0f} MB...", flush=True)
text = open(gry_path, encoding="utf-8").read()
print(f"read in {time.time()-t0:.0f}s; decoding...", flush=True)
dec = json.JSONDecoder()
i = text.index('"graphs"'); i = text.index('[', i) + 1
batch=[]; idx=0
while True:
    while i < len(text) and text[i] in ' \t\r\n,': i += 1
    if i >= len(text) or text[i] == ']': break
    g, i = dec.raw_decode(text, i)
    tr = g.get("trace")
    if tr is None: continue
    idx += 1
    nodes = tr.get("nodes", []); edges = tr.get("edges", [])
    parent = {e["to_id"]: e["from_id"] for e in edges if e.get("relation")=="IN"}
    nmap = {n["id"]: n for n in nodes}
    st = {}
    for n in nodes:
        if n["type"]=="C":
            pid = parent.get(n["id"])
            if pid in nmap:
                lbl = nmap[pid]["label"]
                if lbl in gry_to_col: st[gry_to_col[lbl]] = n["label"]
    batch.append((idx,)+tuple(st.get(c,"") for c in cols))
    if idx % 10000 == 0:
        cur.executemany(f"INSERT INTO trace_states_constrained VALUES ({ph})", batch); batch.clear()
        print(f"  {idx} ({time.time()-t0:.0f}s)", flush=True)
if batch: cur.executemany(f"INSERT INTO trace_states_constrained VALUES ({ph})", batch)
for c in cols: cur.execute(f"CREATE INDEX idx_{c} ON trace_states_constrained({c})")
conn.commit(); conn.close()
print(f"DONE {idx} traces -> {db_path} in {time.time()-t0:.0f}s", flush=True)
