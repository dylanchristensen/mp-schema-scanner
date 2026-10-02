#!/usr/bin/env python3
"""Closed-form MP trace-space enumerator.

Implements the semantics the paper's closed-form checks established:
  * a trace = one state per ROOT, x an inclusion choice for each optional
    ([event]) reachable from the chosen states (each optional doubles variants)
  * presence of an identifier = its state is chosen / its event is emitted
  * REJECT: IF <boolean over #id > 0 / #id == 0, AND/OR/parens> THEN REJECT
  * ENSURE FOREACH $x: a, $y: b ($x BEFORE $y):
      - both events inside the SAME chosen state, grammar order a..b -> holds
      - grammar order b..a inside the same state                    -> deletes
      - a and b in different, uncoordinated ROOTs, both present     -> deletes
        (the trace-deleting mechanism of the smart-home/maritime findings)
  * COORDINATE/PRECEDES blocks add precedence edges only; they do not
    delete traces and are ignored for counting.

Validated against the MP (Firebird) ground truth for the healthcare
(729 -> 36), smart-home (57,600 -> 18,080), and maritime pre-weather
(172,800 -> 45,836) models before use on new models.

Usage:
  python3 mp_enumerate.py <model.mp>            # counts + dead states
  python3 mp_enumerate.py <model.mp> <out.db>   # also write trace_states_constrained
"""
import itertools, re, sqlite3, sys, os
from collections import OrderedDict


def strip_comments(text):
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def parse_mp(path):
    text = strip_comments(open(path, encoding="utf-8").read())

    roots = OrderedDict()
    for m in re.finditer(r"ROOT\s+(\w+)\s*:\s*\(([^;]*?)\)\s*;", text, re.S):
        roots[m.group(1)] = [s.strip() for s in m.group(2).split("|")]
    state_names = {s for sts in roots.values() for s in sts}

    # definitions: name : token token [token] ... ;   (states and sub-events)
    defs = {}
    for m in re.finditer(r"(?m)^\s*(\w+)\s*:\s*([^;()]*?);", text):
        name, body = m.group(1), m.group(2)
        if name in roots:               # ROOT line already handled
            continue
        toks = re.findall(r"(\[?)\s*(\w+)\s*\]?", body)
        defs[name] = [(t, br == "[") for br, t in toks]

    # ENSURE FOREACH $x: a, $y: b ( $i BEFORE $j );
    orderings = []
    for m in re.finditer(
            r"ENSURE\s+FOREACH\s+\$(\w+)\s*:\s*(\w+)\s*,\s*\$(\w+)\s*:\s*(\w+)"
            r"\s*\(\s*\$(\w+)\s+BEFORE\s+\$(\w+)\s*\)\s*;", text):
        v1, e1, v2, e2, b1, b2 = m.groups()
        env = {v1: e1, v2: e2}
        orderings.append((env[b1], env[b2]))

    # IF <cond> THEN REJECT; FI;
    rejects = []
    for m in re.finditer(r"IF\s+(.*?)\s+THEN\s*REJECT\s*;\s*FI\s*;", text, re.S):
        rejects.append(m.group(1).strip())

    return roots, state_names, defs, orderings, rejects


def expand_state(state, defs):
    """DFS expansion -> ordered list of (identifier, frozenset_of_governing_optionals).
    Each optional token is a slot; identifiers under it exist only when included."""
    out = [(state, frozenset())]
    slots = []

    def walk(name, gov):
        for tok, opt in defs.get(name, []):
            g = gov
            if opt:
                slots.append(tok)
                g = gov | {tok}
            out.append((tok, frozenset(g)))
            walk(tok, g)

    walk(state, frozenset())
    return out, slots


def build_variants(roots, defs):
    """Per root: list of (presence frozenset, order dict id->pos, state)."""
    variants = {}
    for root, states in roots.items():
        vs = []
        for st in states:
            items, slots = expand_state(st, defs)
            for included in itertools.chain.from_iterable(
                    itertools.combinations(slots, k) for k in range(len(slots) + 1)):
                inc = set(included)
                seq = [i for i, gov in items if gov <= inc]
                vs.append((frozenset(seq), {e: p for p, e in enumerate(seq)}, st))
        variants[root] = vs
    return variants


def compile_reject(cond, bit):
    expr = re.sub(r"#(\w+)\s*>\s*0", lambda m: f"(P>>{bit[m.group(1)]}&1)", cond)
    expr = re.sub(r"#(\w+)\s*==\s*0", lambda m: f"(not P>>{bit[m.group(1)]}&1)", expr)
    expr = re.sub(r"\bAND\b", "and", expr)
    expr = re.sub(r"\bOR\b", "or", expr)
    return eval(f"lambda P: bool({expr})")  # noqa: S307 — model text, local files


def enumerate_model(path, db_out=None):
    roots, state_names, defs, orderings, rejects = parse_mp(path)
    variants = build_variants(roots, defs)
    root_list = list(roots)

    # identifier -> bit
    idents = set()
    for vs in variants.values():
        for pres, _, _ in vs:
            idents |= pres
    for cond in rejects:
        idents |= set(re.findall(r"#(\w+)", cond))
    idents |= {e for pair in orderings for e in pair}
    bit = {x: i for i, x in enumerate(sorted(idents))}

    # root of each identifier (must be unique across roots)
    ident_root = {}
    for root, vs in variants.items():
        for pres, _, _ in vs:
            for e in pres:
                if e in ident_root and ident_root[e] != root:
                    raise SystemExit(f"identifier {e} appears in roots "
                                     f"{ident_root[e]} and {root}; unsupported")
                ident_root[e] = root

    rej_fns = [compile_reject(c, bit) for c in rejects]

    # ordering pre-analysis
    ord_same, ord_cross = [], []
    for a, b in orderings:
        ra, rb = ident_root.get(a), ident_root.get(b)
        if ra is None or rb is None:
            continue        # event never emitted; constraint vacuous
        if ra == rb:
            ord_same.append((ra, a, b))
        else:
            ord_cross.append((1 << bit[a]) | (1 << bit[b]))

    # per-variant masks + same-root ordering verdicts
    pre = {}
    for root, vs in variants.items():
        rows = []
        for pres, pos, st in vs:
            mask = 0
            for e in pres:
                mask |= 1 << bit[e]
            bad = any(r == root and a in pos and b in pos and pos[a] >= pos[b]
                      for r, a, b in ord_same)
            rows.append((mask, bad, st))
        pre[root] = rows

    total = kept = 0
    survivors = []
    for combo in itertools.product(*(pre[r] for r in root_list)):
        total += 1
        P = 0
        bad = False
        for mask, vbad, _ in combo:
            P |= mask
            bad = bad or vbad
        if bad:
            continue
        if any(P & m == m for m in ord_cross):
            continue
        if any(fn(P) for fn in rej_fns):
            continue
        kept += 1
        if db_out:
            survivors.append(tuple(c[2] for c in combo))

    # support / dead states over survivors
    dead = []
    if db_out:
        seen = {s for row in survivors for s in row}
        dead = [s for r in root_list for s in roots[r] if s not in seen]
        if os.path.exists(db_out):
            os.remove(db_out)
        conn = sqlite3.connect(db_out)
        cols = [r.lower() for r in root_list]
        conn.execute("CREATE TABLE trace_states_constrained (trace_id INTEGER "
                     "PRIMARY KEY, " + ", ".join(f"{c} TEXT" for c in cols) + ")")
        conn.executemany(
            "INSERT INTO trace_states_constrained VALUES (" +
            ",".join("?" * (len(cols) + 1)) + ")",
            [(i + 1,) + tuple(s.replace("_", " ") for s in row)
             for i, row in enumerate(survivors)])
        conn.commit()
        conn.close()

    return dict(model=os.path.basename(path), roots=len(roots),
                rejects=len(rejects), orderings=len(orderings),
                unconstrained=total, constrained=kept, dead=dead)


if __name__ == "__main__":
    import json
    db = sys.argv[2] if len(sys.argv) > 2 else None
    print(json.dumps(enumerate_model(sys.argv[1], db), indent=1))
