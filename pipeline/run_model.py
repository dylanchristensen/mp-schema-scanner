import sqlite3, sys, io, re, contextlib
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from schema_parser import parse_schema
import scanner
from explore_lift import ModelConfig, ForcedPair, analyze

mp_path, db_path = sys.argv[1], sys.argv[2]
schema = parse_schema(mp_path)

def ident_to_state(name):
    if name in schema.state_root: return name
    if name in schema.event_to_state: return schema.event_to_state[name]
    return None
state_col = {s: r.lower() for s, r in schema.state_root.items()}
def sp(s): return s.replace("_", " ")

conn = sqlite3.connect(db_path); cur = conn.cursor()
N = cur.execute("SELECT COUNT(*) FROM trace_states_constrained").fetchone()[0]

# ROOTs absent from trace file (column all empty)
present_cols, missing_roots = [], []
for r in schema.roots.keys():
    c = r.lower()
    nz = cur.execute(f"SELECT COUNT(*) FROM trace_states_constrained WHERE {c} != ''").fetchone()[0]
    if nz > 0: present_cols.append(c)
    else: missing_roots.append(r)
missing_cols = {r.lower() for r in missing_roots}

# symbolic scan + quantify
_, cands = scanner.scan(mp_path)
def quantify(sugg):
    pos = re.findall(r"#(\w+) > 0", sugg); neg = re.findall(r"#(\w+) == 0", sugg)
    if not pos: return None
    ant = ident_to_state(pos[0])
    if ant is None or ant not in state_col: return None
    if state_col[ant] in missing_cols: return None  # antecedent root absent from traces
    where = [f"{state_col[ant]} = '{sp(ant)}'"]; bycol = {}
    for n in neg:
        s = ident_to_state(n)
        if s and s in state_col and state_col[s] not in missing_cols:
            bycol.setdefault(state_col[s], set()).add(sp(s))
    for c, vals in bycol.items():
        inlist = ",".join(f"'{v}'" for v in sorted(vals))
        where.append(f"{c} NOT IN ({inlist})")
    return cur.execute(f"SELECT COUNT(*) FROM trace_states_constrained WHERE {' AND '.join(where)}").fetchone()[0]

scan_rows = []
for shape in ("A","B","C"):
    for c in cands.get(shape, []):
        scan_rows.append((shape, c.get("suggested_reject",""), quantify(c.get("suggested_reject",""))))

# Direction A forced/mutex auto-derive
forced, mutex = [], []
for r in schema.rejects:
    if r.is_single_pos_disjunction():
        x = ident_to_state(r.positives[0])
        for n in r.negatives:
            y = ident_to_state(n)
            if x and y: forced.append(ForcedPair(x,y))
    elif r.is_mutex():
        sts = [s for s in (ident_to_state(p) for p in r.positives) if s]
        for a in range(len(sts)):
            for b in range(a+1,len(sts)): mutex.append(ForcedPair(sts[a],sts[b]))

cfg = ModelConfig(name="m", db_path=db_path, table="trace_states_constrained",
                  components=present_cols, top_k=15, forced=forced, mutex=mutex)
with contextlib.redirect_stdout(io.StringIO()):
    res = analyze(cfg)

# unreachable states within PRESENT roots only
unreachable = []
for s,c in state_col.items():
    if c in missing_cols: continue
    if cur.execute(f"SELECT COUNT(*) FROM trace_states_constrained WHERE {c}='{sp(s)}'").fetchone()[0]==0:
        unreachable.append(s)

print("###N", N)
print("###ROOTS", len(schema.roots), "STATES", len(schema.state_root),
      "ORDERINGS", len(schema.orderings), "REJECTS", len(schema.rejects))
print("###MISSING_ROOTS", "; ".join(missing_roots) if missing_roots else "(none)")
print("###SCAN")
for shape,sugg,cut in scan_rows:
    pct = f"{cut/N:.1%}" if cut is not None else "n/a"
    print(f"{shape}\t{cut}\t{pct}\t{sugg}")
print("###LIFT FORCED", sum(c['forced'] for c in res['candidates']),
      "MUTEX", sum(c['mutex'] for c in res['candidates']),
      "IMPLICIT", len(res['implicit']), "PAIRS", len(res['candidates']))
print("###TOP")
for i,c in enumerate(res['implicit'][:15],1):
    print(f"{i}\t{c['x']}\t{c['y']}\t{c['lift']:.2f}\t{c['conf']:.1%}\t{c['sup_x']:.1%}\t{c['sup_y']:.1%}")
print("###UNREACHABLE", "; ".join(unreachable) if unreachable else "(none)")
conn.close()
