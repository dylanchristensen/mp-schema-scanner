import sys
import os as _os; sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from schema_parser import parse_schema
mp=sys.argv[1]; out=sys.argv[2]; s=parse_schema(mp)
def st(n): return n if n in s.state_root else s.event_to_state.get(n)
COLOR={ "Solar_Inverter":"#fff3cd","EV_System":"#d1ecf1","Home_Battery":"#d4edda",
        "HEMS":"#e2d9f3","Grid_Connection":"#f8d7da","Thermal_Loads":"#ffe5d0","Comm_Gateway":"#d6d8db"}
L=[]
L.append('digraph IAG {')
L.append('  rankdir=LR; fontname="Helvetica"; node [fontname="Helvetica",fontsize=10,style=filled];')
L.append('  edge [fontname="Helvetica",fontsize=8];')
# clusters per ROOT
for root,states in s.roots.items():
    L.append(f'  subgraph cluster_{root} {{ label="{root}"; style=filled; color="#fafafa"; fontsize=11;')
    for st_ in states:
        L.append(f'    "{st_}" [fillcolor="{COLOR.get(root,"#eeeeee")}"];')
    L.append('  }')
orn=0
# requires edges (explicit, solid black); disjunction via OR-diamond
for r in s.rejects:
    if r.is_single_pos_disjunction():
        x=st(r.positives[0]); ys=[st(n) for n in r.negatives]
        if len(ys)==1:
            L.append(f'  "{x}" -> "{ys[0]}" [color=black, label="requires"];')
        else:
            orn+=1; on=f'OR{orn}'
            L.append(f'  {on} [shape=diamond,width=.18,height=.18,label="∨",fillcolor="#ffffff",fontsize=9];')
            L.append(f'  "{x}" -> {on} [color=black,arrowhead=none,label="requires"];')
            for y in ys: L.append(f'  {on} -> "{y}" [color=black];')
    elif r.is_mutex():
        ps=[st(p) for p in r.positives]
        for i in range(len(ps)):
            for j in range(i+1,len(ps)):
                L.append(f'  "{ps[i]}" -> "{ps[j]}" [dir=none,color="#cc0000",style=dashed,label="mutex"];')
    elif r.is_conditional():
        pos=[st(p) for p in r.positives]; neg=[st(n) for n in r.negatives]
        src=[p for p in pos if p!="grid_outage"]
        for sstate in src:
            for y in neg:
                L.append(f'  "{sstate}" -> "{y}" [color="#888888",style=dotted,label="if outage"];')
# orderings (blue)
for a,b in s.orderings:
    xa,xb=st(a),st(b)
    if xa!=xb: L.append(f'  "{xa}" -> "{xb}" [color="#1f6feb",label="before"];')
# DISCOVERED implicit edge (B1: EV charging requires source) -- bold orange
orn+=1; on=f'OR{orn}'
L.append(f'  {on} [shape=diamond,width=.18,height=.18,label="∨",fillcolor="#fff",color="#e8730c",fontsize=9];')
L.append(f'  "vehicle_charging" -> {on} [color="#e8730c",penwidth=2.2,arrowhead=none,label="IMPLICIT (discovered)"];')
for y in ["solar_producing","solar_curtailed","importing_power"]:
    L.append(f'  {on} -> "{y}" [color="#e8730c",penwidth=2.2];')
# legend
L.append('  subgraph cluster_legend { label="Legend"; fontsize=11; style=filled; color="#ffffff";')
L.append('    lk1[shape=plaintext,label="black = explicit requires"];')
L.append('    lk2[shape=plaintext,label="red dashed = mutex"];')
L.append('    lk3[shape=plaintext,label="grey dotted = conditional (outage)"];')
L.append('    lk4[shape=plaintext,label="blue = ordering (before)"];')
L.append('    lk5[shape=plaintext,label="orange bold = discovered implicit edge"];')
L.append('  }')
L.append('}')
open(out,"w").write("\n".join(L))
print("wrote",out)
