import json, sqlite3, os, gc, sys
# usage: python parse_scada.py <Power_Grid_SCADA_Composed_scope_1.gry> <out.db>
# (superseded by pipeline/gry_parse.py, which reads ROOT names from the schema)
GRY, DB = sys.argv[1], sys.argv[2]
COL_NAMES = {
    "Generation Plant":     "generation_plant",
    "Substation Relay IED": "substation_relay_ied",
    "Substation Breaker":   "substation_breaker",
    "SCADA Control Center": "scada_control_center",
    "Transmission Line":    "transmission_line",
    "Distribution Network": "distribution_network",
    "Comm Network":         "comm_network",
    "Smart Meter AMI":      "smart_meter_ami",
}
if os.path.exists(DB): os.remove(DB)
print(f"file size: {os.path.getsize(GRY)/1e6:.1f} MB; loading...")
with open(GRY) as f:
    data = json.load(f)
graphs = data.get("graphs", [])
print(f"top-level graph entries: {len(graphs)}")
conn = sqlite3.connect(DB); conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA synchronous=NORMAL")
cur = conn.cursor()
cols_def = ",\n  ".join(f"{c} TEXT" for c in COL_NAMES.values())
cur.execute(f"CREATE TABLE trace_states_constrained (trace_id INTEGER PRIMARY KEY, {cols_def})")
ph = ",".join("?"*(len(COL_NAMES)+1))
batch=[]; idx=0
for g in graphs:
    tr=g.get("trace")
    if tr is None: continue
    idx+=1
    nodes=tr.get("nodes",[]); edges=tr.get("edges",[])
    parent={e["to_id"]:e["from_id"] for e in edges if e.get("relation")=="IN"}
    nmap={n["id"]:n for n in nodes}
    st={}
    for n in nodes:
        if n["type"]=="C":
            pid=parent.get(n["id"])
            if pid and pid in nmap:
                rl=nmap[pid]["label"]
                if rl in COL_NAMES: st[COL_NAMES[rl]]=n["label"]
    batch.append((idx,)+tuple(st.get(c,"") for c in COL_NAMES.values()))
    if idx%5000==0:
        cur.executemany(f"INSERT INTO trace_states_constrained VALUES ({ph})",batch); batch.clear()
        print(f"  {idx}...")
if batch: cur.executemany(f"INSERT INTO trace_states_constrained VALUES ({ph})",batch)
for c in COL_NAMES.values():
    cur.execute(f"CREATE INDEX idx_{c} ON trace_states_constrained({c})")
conn.commit()
print(f"PARSED {idx} traces -> {DB} ({os.path.getsize(DB)/1e6:.1f} MB)")
del data, graphs; gc.collect()
print("\nState distributions:")
for c in COL_NAMES.values():
    print(f"  {c}:")
    for s,n in cur.execute(f"SELECT {c},COUNT(*) FROM trace_states_constrained GROUP BY {c} ORDER BY COUNT(*) DESC"):
        print(f"     {s}: {n} ({n/idx:.1%})")
conn.close()
