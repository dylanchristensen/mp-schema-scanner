# Implicit Assumption Graph (IAG) — feature design & process

This documents the assumption-graph feature added to the MP Schema Gap
Scanner: what it builds, how each edge is derived, how the SME agent is
used, and how every result is made auditable.

## What it produces

Given a `.mp` schema (and optionally a `.gry` trace file) the tool builds
the **Implicit Assumption Graph**: nodes are component states (grouped by
ROOT), edges are the cross-component dependency assumptions. Two kinds:

- **Explicit edges** — assumptions the designer *wrote down*. Derived
  mechanically from the schema. No LLM, deterministic.
- **Implicit edges** — assumptions the designer *held but never wrote*.
  Discovered by the SME agent reviewing flagged trace patterns.

The graph renders in-browser (self-contained interactive SVG — no
external JS library, so it survives the single-file PyInstaller build).

## Data flow

```
.mp ──parse_schema──► explicit_edges()  ───────────────►┐
                                                         ├──►  IAG (render)
.gry ─parse_gry─► scan() ─► flagged_patterns() ─► SME ──►┘
                              (dedup to worklist)   (per-pattern verdict)
```

1. `/api/assumption_graph` parses the schema, derives explicit edges,
   and (if a `.gry` is given) returns the deduplicated **pattern
   worklist**. No network calls.
2. The browser renders the explicit graph immediately.
3. "Complete with SME" iterates the worklist, calling `/api/sme_pattern`
   once per pattern. Each verdict is parsed; "Missing Assumption" edges
   are added to the graph, every step is written to the process log.

## Edge derivation rules (explicit)

| Schema construct | IAG edge | Type |
|---|---|---|
| `IF #X>0 AND #Y==0 THEN REJECT` | X → Y | `requires` |
| `IF #X>0 AND #Y1==0 AND #Y2==0 …` | X → {Yi} (shared group = "needs at least one") | `requires (or)` |
| `IF #X>0 AND #Y>0 THEN REJECT` | X — Y | `mutex` |
| `IF #X>0 AND #C>0 AND #Y==0 THEN REJECT` | X → Y (labelled "if C") | `conditional` |
| `ENSURE FOREACH …a BEFORE …b` | state(a) → state(b) | `ordering` |

Events are resolved to their owning state, so an event-scoped REJECT
(e.g. on an optional sub-event) lands on the right state node.

## The trace-reduction (why this is reviewable)

A symbolic candidate flags many traces, but they differ only in
irrelevant components. `flagged_patterns()` projects each violating
trace onto **only the components the candidate constrains** and dedupes,
emitting one **review pattern** per distinct projection with a witness
trace. This is what turns thousands of flagged traces into a short
worklist (e.g. healthcare: 36 traces → 4 patterns; smart home in the
field study: ~10k flagged → ~23 patterns). The SME (and the LLM) only
ever look at patterns, not raw traces.

## SME contract (implicit edges)

The agent prompt (unchanged from the existing scanner) returns one of
three verdicts. `parse_sme_verdict()` maps each to a graph action:

| Verdict | Parsed from | Graph action |
|---|---|---|
| **Missing Assumption** | `[State X] -> [State Y]` arrows | add `implicit` edge(s) |
| **Genuine Emergent Behavior** | arrows + gadget/weird-machine text | add `emergent` edge(s), keep gadget text |
| **Modeling Gap** | `IF … REJECT` rule | *no edge* — logged as a suggested REJECT |

Robustness: only arrows whose **both endpoints are real states** in this
schema are accepted, so prose arrows ("A leads to B") never pollute the
graph. Verdict classification is keyword-based and order-aware
(emergent → assumption → gap).

## Provenance (auditability)

Every edge carries a `provenance` object so the finished graph can be
traced back to its source:

- explicit: `{source:"schema", kind, rule}` — the exact REJECT/ordering.
- implicit/emergent: `{source:"sme", model, verdict, pattern_id,
  witness, raw}` — the pattern adjudicated, the model used, and the full
  verdict text.

Click any edge in the UI to see its provenance; the process log records
every pattern → verdict → edge decision of an SME run.

## API

- `POST /api/assumption_graph` (multipart: `schema_file`/`example_schema`,
  optional `traces_file`/`example_traces`) → `{roots, nodes, edges,
  patterns, stats}`.
- `POST /api/sme_pattern` (JSON: `pattern, trace, domain, api_key, model,
  valid_states`) → `{raw, parsed:{verdict,edges,reject,gadget},
  new_edges}`.

## Files

- `assumption_graph.py` — new. Pure logic (graph build, pattern dedup,
  verdict parsing). No Flask/network → unit-testable offline.
- `app.py` — added `_run_sme()` helper (shared by both SME routes),
  `/api/assumption_graph`, `/api/sme_pattern`.
- `templates/index.html` — "Build Assumption Graph" button + graph panel.
- `static/graph.js` — new. Interactive SVG renderer + SME orchestration.
- `static/style.css` — graph view styles (appended).

No new Python dependencies; the PyInstaller spec already bundles
`templates/`, `static/`, `examples/`, so `graph.js` ships automatically.

## Security note

The hardcoded OpenRouter key was removed. The key now comes from the UI
field or the `OPENROUTER_API_KEY` environment variable
(`_DEFAULT_OR_KEY`). Do not commit a real key.
