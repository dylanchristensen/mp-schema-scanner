"""
assumption_graph.py -- build the Implicit Assumption Graph (IAG) for an
MP System-of-Systems model.

The IAG is the central artifact of the INSuRE+C method. Its nodes are
component states; its edges are the cross-component dependency
assumptions the designer holds about those states. There are two kinds
of edge, and this module produces both:

  EXPLICIT edges -- assumptions the designer *wrote down*. Derived
  mechanically from the schema by `explicit_edges()`:
     - "requires"     from REJECT  IF #X>0 AND #Y==0          (X needs Y)
     - "requires(or)" from REJECT  IF #X>0 AND #Y1==0 AND ... (X needs some Yi)
     - "mutex"        from REJECT  IF #X>0 AND #Y>0           (X excludes Y)
     - "conditional"  from REJECT  IF #X>0 AND #C>0 AND #Y==0 (X needs Y given C)
     - "ordering"     from ENSURE FOREACH ... BEFORE ...      (temporal)

  IMPLICIT edges -- assumptions the designer *held but never wrote*.
  These are discovered: the symbolic detectors flag candidate traces,
  the flagged traces are collapsed to a small set of distinct review
  PATTERNS (`flagged_patterns()`), an SME (human or LLM agent) adjudicates
  each pattern, and any "Missing Assumption" verdict yields an implicit
  edge (`parse_sme_verdict()` + `implicit_edges_from_verdict()`).

Every edge carries `provenance` so the finished graph is auditable: an
explicit edge records the schema rule it came from; an implicit edge
records the flagged pattern, the SME verdict text, and the model used.

This module is pure logic (no Flask, no network). The web layer in
app.py calls into it; the SME LLM call itself lives in app.py so this
module stays testable offline.
"""
from __future__ import annotations

import re
from typing import Optional

from schema_parser import parse_schema, Schema
from scanner import (
    parse_gry, candidate_predicate, trace_violates, scan,
)


# --------------------------------------------------------------------- #
# Identifier helpers                                                     #
# --------------------------------------------------------------------- #

def _to_state(schema: Schema, ident: str) -> Optional[str]:
    """Resolve an identifier (state or event) to its owning state."""
    if ident in schema.state_root:
        return ident
    if ident in schema.event_to_state:
        return schema.event_to_state[ident]
    return None


def _root_of(schema: Schema, state: str) -> Optional[str]:
    return schema.state_root.get(state)


# --------------------------------------------------------------------- #
# Nodes                                                                  #
# --------------------------------------------------------------------- #

def node_list(schema: Schema,
              traces: Optional[list] = None) -> list:
    """All states as nodes, grouped by ROOT. If traces are supplied, mark
    each node `reachable` (appears in >=1 trace) so the UI can highlight
    unreachable states -- a common modeling artifact."""
    seen = {}
    if traces:
        for t in traces:
            for st in t.values():
                seen[st] = seen.get(st, 0) + 1
    nodes = []
    for state, root in schema.state_root.items():
        nodes.append({
            "id": state,
            "label": state.replace("_", " "),
            "root": root,
            "reachable": (seen.get(state, 0) > 0) if traces else None,
            "trace_count": seen.get(state, 0) if traces else None,
        })
    return nodes


# --------------------------------------------------------------------- #
# Explicit edges (from the schema)                                       #
# --------------------------------------------------------------------- #

def explicit_edges(schema: Schema) -> list:
    """Derive explicit IAG edges from REJECT rules and orderings."""
    edges = []
    gid = 0

    for r in schema.rejects:
        if r.is_single_pos_disjunction():
            x = _to_state(schema, r.positives[0])
            ys = [_to_state(schema, n) for n in r.negatives]
            ys = [y for y in ys if y]
            if not x or not ys:
                continue
            gid += 1
            group = "req%d" % gid if len(ys) > 1 else None
            for y in ys:
                edges.append({
                    "src": x, "dst": y,
                    "type": "requires",
                    "group": group,
                    "label": "requires" if len(ys) == 1 else "requires (or)",
                    "provenance": {"source": "schema",
                                   "kind": "REJECT (presence)",
                                   "rule": _reject_text(r)},
                })
        elif r.is_mutex():
            states = [_to_state(schema, p) for p in r.positives]
            states = [s for s in states if s]
            for i in range(len(states)):
                for j in range(i + 1, len(states)):
                    edges.append({
                        "src": states[i], "dst": states[j],
                        "type": "mutex", "group": None, "label": "mutex",
                        "provenance": {"source": "schema",
                                       "kind": "REJECT (mutual exclusion)",
                                       "rule": _reject_text(r)},
                    })
        elif r.is_conditional():
            pos = [_to_state(schema, p) for p in r.positives]
            pos = [p for p in pos if p]
            neg = [_to_state(schema, n) for n in r.negatives]
            neg = [n for n in neg if n]
            ctx = [p for p in pos if p in _COMMON_CONTEXT]
            srcs = [p for p in pos if p not in ctx] or pos
            ctx_label = ("if " + " & ".join(c.replace("_", " ") for c in ctx)) \
                if ctx else "conditional"
            for s in srcs:
                for y in neg:
                    if s == y:
                        continue
                    edges.append({
                        "src": s, "dst": y,
                        "type": "conditional", "group": None,
                        "label": ctx_label,
                        "provenance": {"source": "schema",
                                       "kind": "REJECT (conditional)",
                                       "rule": _reject_text(r)},
                    })

    for a, b in schema.orderings:
        xa, xb = _to_state(schema, a), _to_state(schema, b)
        if xa and xb and xa != xb:
            edges.append({
                "src": xa, "dst": xb,
                "type": "ordering", "group": None, "label": "before",
                "provenance": {"source": "schema",
                               "kind": "ENSURE FOREACH (ordering)",
                               "rule": "%s BEFORE %s" % (a, b)},
            })
    return edges


# states that usually act as a context guard rather than the subject of a
# conditional REJECT (extend as needed; purely cosmetic for edge labels).
_COMMON_CONTEXT = {"grid_outage"}


def _reject_text(r) -> str:
    pos = " AND ".join("#%s > 0" % p for p in r.positives)
    neg = " AND ".join("#%s == 0" % n for n in r.negatives)
    body = " AND ".join(x for x in (pos, neg) if x)
    return "IF %s THEN REJECT" % body


# --------------------------------------------------------------------- #
# Flagged-trace -> distinct review PATTERNS                              #
# --------------------------------------------------------------------- #

def flagged_patterns(schema: Schema,
                     candidates_by_shape: dict,
                     traces: list,
                     max_per_candidate: int = 8) -> list:
    """Collapse the flagged trace space into a small SME worklist.

    A symbolic candidate flags many traces, but they differ only in
    irrelevant components. We project each violating trace onto the
    components the candidate actually constrains, dedupe, and emit one
    review PATTERN per distinct projection (with a witness trace). This
    is what turns 'thousands of flagged traces' into 'a handful of
    things to look at'.
    """
    patterns = []
    pid = 0
    for shape in ("A", "B", "C"):
        for c in candidates_by_shape.get(shape, []):
            try:
                pos, neg = candidate_predicate(c)
            except Exception:
                continue
            involved = [pos] + list(neg)
            roots = []
            for s in involved:
                r = _root_of(schema, s)
                if r and r not in roots:
                    roots.append(r)
            buckets = {}
            for t in traces:
                if not trace_violates(t, pos, neg):
                    continue
                key = tuple(t.get(r, "") for r in roots)
                b = buckets.get(key)
                if b is None:
                    buckets[key] = {"count": 1, "witness": t}
                else:
                    b["count"] += 1
            ordered = sorted(buckets.values(), key=lambda b: -b["count"])
            for b in ordered[:max_per_candidate]:
                pid += 1
                patterns.append({
                    "id": "P%d" % pid,
                    "shape": shape,
                    "positive": pos,
                    "negatives": list(neg),
                    "involved_roots": roots,
                    "rationale": c.get("rationale", ""),
                    "suggested_reject": c.get("suggested_reject", ""),
                    "witness": b["witness"],
                    "witness_text": _trace_text(b["witness"]),
                    "trace_count": b["count"],
                })
    return patterns


def _trace_text(states: dict) -> str:
    return ", ".join("%s=%s" % (k, v) for k, v in sorted(states.items()))


# --------------------------------------------------------------------- #
# SME verdict parsing  (text -> structured edges/findings)              #
# --------------------------------------------------------------------- #

_ARROW = re.compile(
    r"\[?\s*([A-Za-z][A-Za-z0-9 _]*?)\s*\]?\s*(?:->|-->|→)\s*"
    r"\[?\s*([A-Za-z][A-Za-z0-9 _]*?)\s*\]?(?=[\s.,;)\]]|$)"
)
_REJECT = re.compile(r"IF\b.*?REJECT", re.IGNORECASE | re.DOTALL)


def classify_verdict(text: str) -> str:
    t = text.lower()
    if "emergent" in t or "weird machine" in t:
        return "emergent"
    if "missing assumption" in t or "implicit assumption" in t:
        return "assumption"
    if "modeling gap" in t or "model is wrong" in t or "model is incomplete" in t:
        return "gap"
    return "unknown"


def parse_sme_verdict(text: str, schema: Optional[Schema] = None,
                      valid_states: Optional[set] = None) -> dict:
    """Parse a free-text SME/LLM verdict into structured findings.

    Returns {verdict, edges:[(x,y)], reject, gadget, raw}. Only arrows
    whose endpoints are real states are kept, so prose arrows
    ('A -> B means ...') don't pollute the graph. Endpoints are resolved
    against `schema` (states + events) if given, else against the
    `valid_states` set (the graph's node ids).
    """
    def resolve(ident):
        if schema is not None:
            return _to_state(schema, ident)
        if valid_states is not None:
            return ident if ident in valid_states else None
        return ident

    verdict = classify_verdict(text)
    edges = []
    for m in _ARROW.finditer(text):
        x = m.group(1).strip().replace(" ", "_")
        y = m.group(2).strip().replace(" ", "_")
        xs, ys = resolve(x), resolve(y)
        if xs and ys and xs != ys and (xs, ys) not in edges:
            edges.append((xs, ys))
    reject = None
    rm = _REJECT.search(text)
    if rm:
        reject = re.sub(r"\s+", " ", rm.group(0)).strip()
    gadget = None
    if verdict == "emergent":
        gm = re.search(r"(gadget|weird machine)(.*)", text,
                       re.IGNORECASE | re.DOTALL)
        if gm:
            gadget = gm.group(0).strip()[:1000]
    return {"verdict": verdict, "edges": edges,
            "reject": reject, "gadget": gadget, "raw": text}


def implicit_edges_from_verdict(parsed: dict, pattern: dict,
                                model: str = "") -> list:
    """Turn a parsed verdict + the pattern it adjudicated into IAG edges
    with full provenance.

    The pattern itself *is* the candidate dependency: it flags "positive
    present without negative", i.e. positive -> negative. So when the SME
    gives a positive verdict but the free-text reply contains no clean
    "[X] -> [Y]" arrow (common with small models), we fall back to the
    pattern's own positive -> negatives pairs. Mapping:
      Missing Assumption    -> implicit edge(s)
      Genuine Emergent      -> emergent edge(s) (carry gadget text)
      Modeling Gap          -> proposed edge(s) (carry suggested REJECT)
      false positive/other  -> no edge
    """
    out = []
    prov_base = {
        "source": "sme",
        "model": model,
        "verdict": parsed["verdict"],
        "pattern_id": pattern.get("id"),
        "witness": pattern.get("witness"),
        "raw": parsed["raw"],
    }
    pos = pattern.get("positive")
    negs = pattern.get("negatives") or []
    pattern_pairs = [(pos, n) for n in negs if pos and n]

    def emit(pairs, etype, label, extra=None):
        for (x, y) in pairs:
            d = dict(prov_base)
            if extra:
                d.update(extra)
            out.append({"src": x, "dst": y, "type": etype, "group": None,
                        "label": label, "provenance": d})

    v = parsed["verdict"]
    if v == "assumption":
        emit(parsed["edges"] or pattern_pairs, "implicit", "implicit (SME)")
    elif v == "emergent":
        emit(parsed["edges"] or pattern_pairs, "emergent", "emergent (gadget)",
             {"gadget": parsed.get("gadget")})
    elif v == "gap":
        emit(parsed["edges"] or pattern_pairs, "proposed",
             "proposed REJECT (gap)", {"suggested_reject": parsed.get("reject")})
    return out


# --------------------------------------------------------------------- #
# Top-level assembly (explicit graph + worklist)                        #
# --------------------------------------------------------------------- #

def build(schema_path: str, gry_path: Optional[str] = None) -> dict:
    """Build the explicit IAG and (if traces given) the SME worklist.
    The implicit edges are added later, one SME call per pattern, by the
    web layer -- this function does no network I/O."""
    schema, cands = scan(schema_path, gry_path)
    traces = parse_gry(gry_path, schema) if gry_path else None
    return {
        "roots": list(schema.roots.keys()),
        "nodes": node_list(schema, traces),
        "edges": explicit_edges(schema),
        "patterns": flagged_patterns(schema, cands, traces) if traces else [],
        "stats": {
            "states": len(schema.state_root),
            "rejects": len(schema.rejects),
            "orderings": len(schema.orderings),
            "trace_count": len(traces) if traces else 0,
        },
    }


# --------------------------------------------------------------------- #
# Offline self-test                                                      #
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    import sys
    mp = sys.argv[1]
    gry = sys.argv[2] if len(sys.argv) > 2 else None
    g = build(mp, gry)
    print("roots=%d nodes=%d explicit_edges=%d patterns=%d" % (
        len(g["roots"]), len(g["nodes"]), len(g["edges"]), len(g["patterns"])))
    by_type = {}
    for e in g["edges"]:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
    print("edge types:", by_type)
    unreachable = [n["id"] for n in g["nodes"] if n["reachable"] is False]
    if unreachable:
        print("unreachable states:", unreachable)
    if g["patterns"]:
        print("first review patterns:")
        for p in g["patterns"][:5]:
            print("  %s [%s] %s !-> %s (x%d) witness: %s" % (
                p["id"], p["shape"], p["positive"], p["negatives"],
                p["trace_count"], p["witness_text"][:80]))
    schema = parse_schema(mp)
    demo = ("Verdict: Missing Assumption. "
            "Implicit Assumption Edge: [vehicle_charging] -> [importing_power]")
    print("parser demo:", parse_sme_verdict(demo, schema))
