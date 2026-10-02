"""
explore_lift.py -- generalized single-set lift+confidence+support analysis
for implicit-assumption discovery in MP-modeled Systems of Systems.

This is the procedure committed to as Direction A for milestone M2 (see
Summer/Two_Directions_Decision_Memo.docx.pdf and the response chat). It
replaces the earlier Summer/_archive/superseded-scripts/cooccurrence_formal.py
by adding the schema-derived REJECT-forced filter, which is what makes
single-set lift answer "different from intended" directly rather than
"different from random."

Per-model scripts (explore_lift_healthcare.py, explore_lift_smart_home.py)
construct a ModelConfig and call analyze(config). The procedure is locked
here so per-model scripts cannot accidentally change it; they only supply
data (schema components, REJECT-forced pairs, validation entries).

Procedure (locked BEFORE looking at any output, for every model):
  1. All cross-ROOT ordered pairs (X, Y) where component(X) != component(Y).
  2. Filter pairs by support: support(X) >= K/N and support(Y) >= K/N,
     where K = ModelConfig.min_support_count (default 3).
  3. Annotate which surviving pairs are forced by an explicit REJECT.
     Lift is symmetric -- forcing (X, Y) implies forcing (Y, X), so the
     "forced" set is closed under transposition.
  4. Rank surviving (not-forced, not-mutex) pairs by lift desc; top
     ModelConfig.top_k are the implicit-assumption candidates.
  5. THEN look up where the model's validation set lands (Spring's known
     assumptions, or pre-registered candidates from a schema sketch).

Forced filter handles partial-mandate REJECTs of the form
"X > 0 AND no Y_i" (X requires at least one Y_i): each (X, Y_i) is a
partially-forced pair and is excluded from the implicit ranking.

Mutex filter handles REJECTs of the form "X > 0 AND Y > 0"
(X and Y mutually exclude): each (X, Y) is forced-absent and is also
excluded.

NOT yet handled: compositional forced pairs -- those induced by REJECTs
in combination but not by any single REJECT. That is the roadmap
"leave-one-out" refinement; it would add additional entries to the
forced set before the lift ranking is taken.
"""

import sqlite3
from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass
class ForcedPair:
    """A pair (x, y) where the schema's REJECT rules force a partial or
    mutex relationship. `note` is free text -- typically the REJECT
    rule's identifier or a one-line summary."""
    x: str
    y: str
    note: str = ""


@dataclass
class ValidationEntry:
    """A pair to look up in the ranking after analysis, with a label.
    Used for blind validation: Spring's known implicit assumptions for
    the healthcare model, pre-registered schema-sketch candidates for
    new models."""
    x: str
    y: str
    label: str


@dataclass
class ModelConfig:
    name: str
    db_path: str
    table: str
    components: Sequence[str]
    expected_n: Optional[int] = None
    min_support_count: int = 3
    top_k: int = 25
    normalize_underscores: bool = True
    forced: Sequence[ForcedPair] = field(default_factory=list)
    mutex: Sequence[ForcedPair] = field(default_factory=list)
    validation: Sequence[ValidationEntry] = field(default_factory=list)
    validation_label: str = "VALIDATION ENTRIES"


def _normalize(x: str, y: str, on: bool):
    if on:
        return x.replace("_", " "), y.replace("_", " ")
    return x, y


def _build_forced_set(pairs: Sequence[ForcedPair],
                      normalize_underscores: bool):
    """Build a transposition-closed set of (x, y) pairs from a ForcedPair
    list. Lift is symmetric, so excluding (X, Y) must also exclude (Y, X)."""
    s = set()
    for p in pairs:
        x, y = _normalize(p.x, p.y, normalize_underscores)
        s.add((x, y))
        s.add((y, x))
    return s


def load_traces(db_path: str, table: str, components: Sequence[str]):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"SELECT {', '.join(components)} FROM {table}")
    rows = cur.fetchall()
    conn.close()
    return rows


def _state_to_component(rows, components):
    m = {}
    for r in rows:
        for i, comp in enumerate(components):
            m[r[i]] = comp
    return m


def _count_singletons(rows, states):
    counts = {s: 0 for s in states}
    for r in rows:
        for s in set(r):
            counts[s] += 1
    return counts


def _count_pairs(rows, state_comp):
    pair_counts = {}
    for r in rows:
        present = set(r)
        for x in present:
            for y in present:
                if x == y or state_comp[x] == state_comp[y]:
                    continue
                pair_counts[(x, y)] = pair_counts.get((x, y), 0) + 1
    return pair_counts


def analyze(config: ModelConfig):
    """Run the locked procedure on `config` and print results to stdout.
    Returns a dict with N, candidates, implicit (ranked), and full (ranked)
    for downstream consumers."""
    rows = load_traces(config.db_path, config.table, config.components)
    N = len(rows)
    print(f"[{config.name}] Loaded {N} constrained traces.")
    if config.expected_n is not None:
        assert N == config.expected_n, (
            f"Expected {config.expected_n} traces, got {N}"
        )

    state_comp = _state_to_component(rows, config.components)
    count_x = _count_singletons(rows, state_comp.keys())
    pair_count = _count_pairs(rows, state_comp)

    forced = _build_forced_set(config.forced, config.normalize_underscores)
    mutex = _build_forced_set(config.mutex, config.normalize_underscores)

    min_sup = config.min_support_count / N
    candidates = []
    for (x, y), cxy in pair_count.items():
        sx = count_x[x] / N
        sy = count_x[y] / N
        if sx < min_sup or sy < min_sup:
            continue
        sxy = cxy / N
        conf = cxy / count_x[x] if count_x[x] > 0 else 0.0
        lift = sxy / (sx * sy) if sx * sy > 0 else 0.0
        candidates.append({
            "x": x, "y": y,
            "sup_x": sx, "sup_y": sy, "sup_xy": sxy,
            "conf": conf, "lift": lift,
            "forced": (x, y) in forced,
            "mutex": (x, y) in mutex,
        })

    implicit = sorted(
        [c for c in candidates if not c["forced"] and not c["mutex"]],
        key=lambda c: -c["lift"],
    )
    full = sorted(candidates, key=lambda c: -c["lift"])

    n_forced = sum(1 for c in candidates if c["forced"])
    n_mutex = sum(1 for c in candidates if c["mutex"])

    print(f"\nTotal cross-ROOT ordered pairs: {len(pair_count)}")
    print(f"After support filter (>= {min_sup:.1%}): {len(candidates)}")
    print(f"  forced by explicit REJECTs: {n_forced}")
    print(f"  mutex by explicit REJECTs:  {n_mutex}")
    print(f"  surviving implicit candidates: {len(implicit)}")

    print("\n" + "=" * 100)
    print(f"TOP {config.top_k} IMPLICIT CANDIDATES "
          "(forced + mutex removed, ranked by lift)")
    print("=" * 100)
    print(f"{'rank':>4}  {'X':>30}  ->  {'Y':<30}  "
          f"{'lift':>6}  {'conf':>6}  {'sup(x)':>7}  {'sup(y)':>7}")
    print("-" * 100)
    for i, c in enumerate(implicit[:config.top_k], 1):
        print(f"{i:>4}  {c['x']:>30}  ->  {c['y']:<30}  "
              f"{c['lift']:>6.2f}  {c['conf']:>6.1%}  "
              f"{c['sup_x']:>7.1%}  {c['sup_y']:>7.1%}")

    if config.validation:
        _print_validation(config, count_x, pair_count, N,
                          implicit, full)

    return {
        "N": N,
        "candidates": candidates,
        "implicit": implicit,
        "full": full,
    }


def _print_validation(config, count_x, pair_count, N, implicit, full):
    rank_lookup = {(c["x"], c["y"]): (i, c)
                   for i, c in enumerate(implicit, 1)}
    full_lookup = {(c["x"], c["y"]): (i, c)
                   for i, c in enumerate(full, 1)}

    print("\n" + "=" * 100)
    print(f"{config.validation_label} -- where they land in the ranking")
    print("=" * 100)
    for v in config.validation:
        x, y = _normalize(v.x, v.y, config.normalize_underscores)
        print(f"  {x} -> {y}   [{v.label}]")
        implicit_info = rank_lookup.get((x, y))
        full_info = full_lookup.get((x, y))
        if implicit_info is not None:
            rank, c = implicit_info
            fr = full_info[0] if full_info else None
            fr_str = (f"  (full rank {fr}/{len(full)})"
                      if fr is not None else "")
            print(f"    rank {rank}/{len(implicit)}{fr_str}   "
                  f"lift={c['lift']:.2f}  conf={c['conf']:.1%}  "
                  f"sup(x)={c['sup_x']:.1%}  sup(x,y)={c['sup_xy']:.1%}")
        elif full_info is not None:
            fr, c = full_info
            tag = "forced" if c["forced"] else ("mutex" if c["mutex"] else "?")
            print(f"    excluded from implicit ranking ({tag}); "
                  f"full rank {fr}/{len(full)}   "
                  f"lift={c['lift']:.2f}  conf={c['conf']:.1%}  "
                  f"sup(x,y)={c['sup_xy']:.1%}")
        else:
            sx = count_x.get(x, 0) / N
            sy = count_x.get(y, 0) / N
            cxy = pair_count.get((x, y), 0)
            print(f"    NOT IN CANDIDATE SET. "
                  f"sup(x)={sx:.1%} sup(y)={sy:.1%} count(x,y)={cxy}")
        print()
