#!/usr/bin/env python3
"""CHIMERA co-occurrence anomaly flag — paper configuration (Section 4/7).

Replicates the published criterion on a trace_states_constrained DB:
  * family = unordered cross-component state pairs, both states support>0
  * 2x2 contingency table per pair over the constrained trace space
  * odds ratio with Haldane-Anscombe correction (0.5 per cell)
  * 95% CI on log OR excluding 0  ->  "trend" (clinging / excluding)
  * Fisher's exact test (two-sided) on the uncorrected table
  * Bonferroni and Benjamini-Hochberg at alpha = 0.05 over the family
  * zero-support state audit against the .mp schema
  * pre-classification: pairs mentioned together by a single REJECT rule

Usage: python3 run_cooccurrence_pipeline.py <model.mp> <traces.db> <out.md> <name>
"""
import json, math, sqlite3, sys, os
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "mp-schema-scanner"))
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
from schema_parser import parse_schema

ALPHA = 0.05
Z95 = 1.959963984540054

_LF = None  # cumulative log-factorial table


def _lf_table(n):
    global _LF
    if _LF is None or len(_LF) <= n:
        _LF = np.cumsum(np.concatenate(([0.0], np.log(np.arange(1, n + 1)))))
    return _LF


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher's exact test, 'sum of small p' convention
    (scipy-compatible), vectorized over the hypergeometric support."""
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2
    LF = _lf_table(n + 1)
    lo, hi = max(0, c1 - r2), min(c1, r1)
    ks = np.arange(lo, hi + 1)
    logp = (LF[r1] - LF[ks] - LF[r1 - ks]
            + LF[r2] - LF[c1 - ks] - LF[r2 - c1 + ks]
            - (LF[n] - LF[c1] - LF[n - c1]))
    p_obs = logp[a - lo]
    return float(min(1.0, np.exp(logp[logp <= p_obs + 1e-7]).sum()))


def bh_survivors(pvals, alpha=ALPHA):
    """Return set of indices surviving Benjamini-Hochberg at alpha."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    cutoff = -1
    for rank, i in enumerate(order, 1):
        if pvals[i] <= alpha * rank / m:
            cutoff = rank
    return set(order[:cutoff]) if cutoff > 0 else set()


def run(mp_path, db_path, out_path, name):
    schema = parse_schema(mp_path)
    roots = list(schema.roots.keys())
    cols = [r.lower() for r in roots]
    label_of = {}   # db label -> schema state
    root_of = {}    # schema state -> root
    for r in roots:
        for st in schema.roots[r]:
            label_of[st.replace("_", " ")] = st
            root_of[st] = r

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    db_cols = [r[1] for r in cur.execute("PRAGMA table_info(trace_states_constrained)")][1:]
    rows = cur.execute(
        "SELECT " + ", ".join(db_cols) + " FROM trace_states_constrained").fetchall()
    N = len(rows)

    # support per state (schema names)
    support = Counter()
    for row in rows:
        for v in row:
            if v:
                support[label_of.get(v, v)] += 1
    dead = [st for r in roots for st in schema.roots[r] if support[st] == 0]

    # joint counts per cross-root column pair
    col_idx = {c: i for i, c in enumerate(db_cols)}
    pairs = []  # (state_a, state_b, n11, n1_, n_1)
    for i in range(len(db_cols)):
        for j in range(i + 1, len(db_cols)):
            joint = Counter((row[i], row[j]) for row in rows)
            marg_i = Counter(row[i] for row in rows)
            marg_j = Counter(row[j] for row in rows)
            for la, ca in marg_i.items():
                if not la:
                    continue
                for lb, cb in marg_j.items():
                    if not lb:
                        continue
                    pairs.append((label_of.get(la, la), label_of.get(lb, lb),
                                  joint.get((la, lb), 0), ca, cb))

    m = len(pairs)
    results = []
    for sa, sb, n11, n1_, n_1 in pairs:
        n10, n01 = n1_ - n11, n_1 - n11
        n00 = N - n11 - n10 - n01
        a, b, c, d = n11 + 0.5, n10 + 0.5, n01 + 0.5, n00 + 0.5
        lor = math.log(a * d / (b * c))
        se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
        trend = abs(lor) > Z95 * se
        p = fisher_two_sided(n11, n10, n01, n00)
        results.append(dict(a=sa, b=sb, n11=n11, n10=n10, n01=n01, n00=n00,
                            OR=math.exp(lor), logOR=lor, trend=trend, p=p))

    pvals = [r["p"] for r in results]
    bonf = {i for i, p in enumerate(pvals) if p < ALPHA / m}
    bh = bh_survivors(pvals)

    # schema-mentioned pre-classification (single REJECT names both states)
    ev2st = getattr(schema, "event_to_state", {}) or {}
    def to_states(idents):
        out = set()
        for x in idents:
            if x in root_of:
                out.add(x)
            elif x in ev2st and ev2st[x] in root_of:
                out.add(ev2st[x])
        return out
    reject_sets = [to_states(rj.positives) | to_states(rj.negatives)
                   for rj in schema.rejects]
    def forced(sa, sb):
        return any(sa in s and sb in s for s in reject_sets)
    for r in results:
        r["schema_mentioned"] = forced(r["a"], r["b"])

    trends = [r for r in results if r["trend"]]
    cling = [r for r in trends if r["logOR"] > 0]
    excl = [r for r in trends if r["logOR"] < 0]

    # ---- report ----
    L = []
    L.append(f"# {name} — Co-occurrence Anomaly Flag (paper configuration)\n")
    L.append(f"**Model:** `{os.path.basename(mp_path)}` ({len(roots)} ROOTs, "
             f"{sum(len(v) for v in schema.roots.values())} states, "
             f"{len(schema.rejects)} REJECTs, {len(schema.orderings)} orderings)")
    L.append(f"**Traces:** {N:,} constrained (`{os.path.basename(db_path)}`)")
    L.append(f"**Criterion:** odds ratio (Haldane–Anscombe), 95% CI gate, "
             f"Fisher exact, Bonferroni + BH at α={ALPHA}\n")
    L.append("## Summary\n")
    L.append(f"| Family (m) | Trends | Clinging | Excluding | Bonferroni | BH |")
    L.append(f"|---:|---:|---:|---:|---:|---:|")
    L.append(f"| {m} | {len(trends)} | {len(cling)} | {len(excl)} | {len(bonf)} | {len(bh)} |\n")
    if dead:
        L.append("## Zero-support states (structural audit)\n")
        for st in dead:
            L.append(f"- `{st}` ({root_of[st]}) — occurs in 0 of {N:,} traces")
        L.append("")
    L.append("## Top 25 trends by |log OR|\n")
    L.append("| Pair | OR | n11 | p (Fisher) | Bonf | BH | REJECT-mentioned |")
    L.append("|---|---:|---:|---:|:--:|:--:|:--:|")
    idx_of = {id(r): i for i, r in enumerate(results)}
    for r in sorted(trends, key=lambda r: -abs(r["logOR"]))[:25]:
        i = idx_of[id(r)]
        L.append(f"| `{r['a']}` ↔ `{r['b']}` | {r['OR']:.2f} | {r['n11']:,} | "
                 f"{r['p']:.2e} | {'✓' if i in bonf else ''} | {'✓' if i in bh else ''} | "
                 f"{'✓' if r['schema_mentioned'] else ''} |")
    L.append("")
    n_forced = sum(1 for r in trends if r["schema_mentioned"])
    L.append(f"Of {len(trends)} trends, **{n_forced}** involve a state pair named together "
             f"by a single `REJECT` rule (schema-mentioned; prime schema-induced candidates). "
             f"The remaining {len(trends)-n_forced} need SME adjudication.\n")
    L.append("*Note:* ordering (`ENSURE FOREACH`) vacuity is event-level and not checkable "
             "from the state DB; the zero-support audit above catches its trace-deleting form.\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    return dict(name=name, N=N, m=m, trends=len(trends), cling=len(cling),
                excl=len(excl), bonf=len(bonf), bh=len(bh), dead=dead)


if __name__ == "__main__":
    print(json.dumps(run(*sys.argv[1:5]), indent=1))
