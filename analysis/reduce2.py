import sqlite3, sys, re
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from schema_parser import parse_schema
import scanner
mp, db = sys.argv[1], sys.argv[2]
s = parse_schema(mp)
cols=[r.lower() for r in s.roots.keys()]
state_col={st:r.lower() for st,r in s.state_root.items()}
def sp(x): return x.replace('_',' ')
def i2s(n): return n if n in s.state_root else s.event_to_state.get(n)
con=sqlite3.connect(db); cur=con.cursor()
N=cur.execute("SELECT COUNT(*) FROM trace_states_constrained").fetchone()[0]
_,cands=scanner.scan(mp)
rows=[]
total_flagged=set(); total_patterns=0
for shape in("A","B","C"):
    for c in cands.get(shape,[]):
        sugg=c.get("suggested_reject","")
        pos=re.findall(r"#(\w+) > 0",sugg); neg=re.findall(r"#(\w+) == 0",sugg)
        if not pos: continue
        ant=i2s(pos[0])
        if not ant or ant not in state_col: continue
        acol=state_col[ant]
        bycol={}
        for n in neg:
            st=i2s(n)
            if st and st in state_col: bycol.setdefault(state_col[st],set()).add(sp(st))
        where=[f"{acol}='{sp(ant)}'"]
        involved={acol}
        for cc,vals in bycol.items():
            where.append(f"{cc} NOT IN ({','.join(repr(v) for v in sorted(vals))})")
            involved.add(cc)
        w=" AND ".join(where)
        involved=sorted(involved)
        flagged=cur.execute(f"SELECT trace_id FROM trace_states_constrained WHERE {w}").fetchall()
        nflag=len(flagged)
        if nflag==0: continue
        # distinct patterns on involved components
        pats=cur.execute(f"SELECT DISTINCT {','.join(involved)} FROM trace_states_constrained WHERE {w}").fetchall()
        rows.append((shape,ant,sorted(set().union(*bycol.values())) if bycol else [],nflag,len(pats),involved))
        for (tid,) in flagged: total_flagged.add(tid)
        total_patterns+=len(pats)
print(f"trace space N = {N}")
print(f"detection signals (symbolic candidates with >=1 flagged trace): {len(rows)}")
print(f"union of flagged traces: {len(total_flagged)}  ({len(total_flagged)/N:.0%} of space)")
print(f"distinct review PATTERNS (flagged traces projected onto each edge's components): {total_patterns}")
print(f"\n{'signal':<7}{'antecedent (present)':<26}{'flagged':>9}{'patterns':>10}  involved-components")
print('-'*95)
for shape,ant,req,nflag,npat,inv in sorted(rows,key=lambda r:-r[3]):
    print(f"{shape:<7}{ant:<26}{nflag:>9}{npat:>10}  {','.join(inv)}")
con.close()
