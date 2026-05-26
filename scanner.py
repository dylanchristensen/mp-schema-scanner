"""
scanner.py -- single-entrypoint schema/trace scanner.

Usage:
    python scanner.py <schema.mp> [<traces.gry>] [--out report.md]

Given an MP schema and (optionally) a Gryphon trace file, this script:

  1. Parses the schema into structured form (ROOTs, states, events,
     REJECTs, ENSURE FOREACH orderings).
  2. Runs three symbolic detectors that surface candidate REJECT rules
     the schema is missing:
        Shape A -- vacuous-foreach gap (formalized Signal 2)
        Shape B -- symmetric REJECT completion (structural Signal 3)
        Shape C -- optional-event escalation (event-scope Signal 3)
  3. If a .gry file is provided, for each candidate it computes the
     trace evidence: how many traces in the file would be eliminated
     by the proposed rule, plus a small sample of violating traces.
  4. Prints a structured report to stdout, optionally also writing
     Markdown to --out.

This is a draft-stage SME aid: every candidate is a SUGGESTION for
SME review, not an auto-applied fix. The SME decides whether each
candidate is (a) a real schema gap to promote to a REJECT, (b) an
implicit assumption to record in the Assumption Graph, or (c) a
false positive to dismiss with rationale.
"""
from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass

from schema_parser import parse_schema, Schema
from symbolic_detector import (
    detect_shape_a, detect_shape_b, detect_shape_c,
)


# Generic .gry parsing -------------------------------------------------

def parse_gry(gry_path: str, schema: Schema) -> list[dict[str, str]]:
    """Parse a Gryphon JSON trace file into a list of dict-of-dicts.

    Each trace is returned as {root_name -> state_name}. ROOT names are
    taken from the schema; the .gry file uses spaces in its labels
    (e.g., 'Clinical Device' for ROOT Clinical_Device), so we match by
    converting underscores to spaces.
    """
    label_to_root = {r.replace("_", " "): r for r in schema.roots}
    state_set = set(schema.state_root)

    with open(gry_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = []
    for g in data.get("graphs", []):
        trace = g.get("trace")
        if trace is None:
            continue
        nodes = trace.get("nodes", [])
        edges = trace.get("edges", [])

        parent_map = {}
        for edge in edges:
            if edge.get("relation") == "IN":
                parent_map[edge["to_id"]] = edge["from_id"]
        node_map = {n["id"]: n for n in nodes}

        states = {}
        for node in nodes:
            if node["type"] != "C":
                continue
            pid = parent_map.get(node["id"])
            if not pid or pid not in node_map:
                continue
            root_label = node_map[pid]["label"]
            root = label_to_root.get(root_label)
            if not root:
                continue
            # .gry labels have spaces; schema uses underscores.
            state_label = node["label"]
            state_underscored = state_label.replace(" ", "_")
            if state_underscored in state_set:
                states[root] = state_underscored
            else:
                # Fall back to raw label if parser can't resolve.
                states[root] = state_label

        if states:
            out.append(states)
    return out


# Candidate -> (positive, negatives) extraction ------------------------

def candidate_predicate(cand: dict) -> tuple[str, list[str]]:
    """Return (positive_state, [negative_states]) for a candidate."""
    if cand["shape"] == "A":
        positive = cand["x_b"]
        negatives = sorted({cand["x_a"]} | set(cand["alt_sources"]))
    elif cand["shape"] == "B":
        positive = cand["candidate_state"]
        negatives = list(cand["analog_of"][1])
    elif cand["shape"] == "C":
        positive = cand["parent_state"]
        negatives = list(cand["source_set"])
    else:
        raise ValueError(f"unknown shape: {cand['shape']}")
    return positive, negatives


def trace_violates(trace: dict[str, str], positive: str,
                   negatives: list[str]) -> bool:
    """Trace breaks the proposed rule iff positive is present AND no
    element of negatives is present."""
    states = set(trace.values())
    if positive not in states:
        return False
    if any(neg in states for neg in negatives):
        return False
    return True


def evidence_for(cand: dict, traces: list[dict[str, str]],
                 sample_size: int = 3) -> dict:
    pos, neg = candidate_predicate(cand)
    violators_idx = [
        i for i, t in enumerate(traces) if trace_violates(t, pos, neg)
    ]
    sample = []
    for i in violators_idx[:sample_size]:
        sample.append({"trace_id": i + 1, "states": traces[i]})
    return {
        "violation_count": len(violators_idx),
        "trace_count": len(traces),
        "sample": sample,
        "violation_rate": (
            len(violators_idx) / len(traces) if traces else 0.0
        ),
    }


# Report ---------------------------------------------------------------

def _fmt_trace_states(states: dict[str, str]) -> str:
    parts = [f"{k}={v}" for k, v in sorted(states.items())]
    return ", ".join(parts)


def _shape_header(shape: str) -> str:
    return {
        "A": "Shape A -- vacuous-foreach gaps",
        "B": "Shape B -- symmetric REJECT completion",
        "C": "Shape C -- optional-event escalation",
    }[shape]


def render_report(schema_path: str, gry_path: str | None,
                  schema: Schema, candidates_by_shape: dict[str, list],
                  use_markdown: bool = False) -> str:
    lines = []
    h = "##" if use_markdown else "="
    sub = "###" if use_markdown else "-"

    def header(text):
        if use_markdown:
            lines.append(f"## {text}")
            lines.append("")
        else:
            lines.append("")
            lines.append("=" * 80)
            lines.append(text)
            lines.append("=" * 80)

    def subheader(text):
        if use_markdown:
            lines.append(f"### {text}")
            lines.append("")
        else:
            lines.append("")
            lines.append("-" * 80)
            lines.append(text)
            lines.append("-" * 80)

    header(f"INSuRE+C Schema Scanner")
    lines.append(f"Schema:  {schema_path}")
    lines.append(f"Traces:  {gry_path or '(none provided)'}")
    lines.append(f"States:  {len(schema.state_root)}  "
                 f"Orderings: {len(schema.orderings)}  "
                 f"REJECTs: {len(schema.rejects)}")
    lines.append("")

    total = sum(len(v) for v in candidates_by_shape.values())
    lines.append(f"Total candidate findings: {total}")
    for s, lst in candidates_by_shape.items():
        lines.append(f"  Shape {s}: {len(lst)}")
    lines.append("")

    for shape in ("A", "B", "C"):
        cands = candidates_by_shape[shape]
        subheader(_shape_header(shape))
        if not cands:
            lines.append("(no candidates)")
            lines.append("")
            continue
        for i, c in enumerate(cands, 1):
            lines.append(f"{shape}{i}. {c['rationale']}")
            lines.append(f"    Suggested REJECT:")
            lines.append(f"        IF {c['suggested_reject']}; FI;")
            ev = c.get("evidence")
            if ev is not None:
                pct = ev["violation_rate"] * 100
                lines.append(
                    f"    Trace evidence: "
                    f"{ev['violation_count']} of {ev['trace_count']} "
                    f"traces violate this proposed rule "
                    f"({pct:.1f}%)"
                )
                for s in ev["sample"]:
                    lines.append(
                        f"        trace #{s['trace_id']}: "
                        f"{_fmt_trace_states(s['states'])}"
                    )
            lines.append("")
    return "\n".join(lines)


# Main -----------------------------------------------------------------

def scan(schema_path: str, gry_path: str | None = None) -> tuple[Schema, dict]:
    schema = parse_schema(schema_path)
    candidates_by_shape = {
        "A": detect_shape_a(schema),
        "B": detect_shape_b(schema),
        "C": detect_shape_c(schema),
    }
    # Sort Shape B with cross-ROOT analogies first.
    candidates_by_shape["B"].sort(
        key=lambda c: (c["analogy"] != "shared-token analog",
                       c["candidate_state"])
    )

    if gry_path:
        print(f"Loading {gry_path}...", file=sys.stderr)
        traces = parse_gry(gry_path, schema)
        print(f"Parsed {len(traces)} traces.", file=sys.stderr)
        for shape in candidates_by_shape:
            for c in candidates_by_shape[shape]:
                c["evidence"] = evidence_for(c, traces)
    return schema, candidates_by_shape


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    schema_path = argv[1]
    gry_path = None
    out_path = None
    i = 2
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_path = argv[i + 1]
            i += 2
        elif argv[i].endswith(".gry"):
            gry_path = argv[i]
            i += 1
        else:
            print(f"unrecognized argument: {argv[i]}", file=sys.stderr)
            return 2

    schema, cands = scan(schema_path, gry_path)
    report = render_report(
        schema_path, gry_path, schema, cands,
        use_markdown=(out_path is not None and out_path.endswith(".md")),
    )
    print(report)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nWrote report to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
