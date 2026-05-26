# MP Schema Gap Scanner

A small tool for finding missing assumptions in Monterey Phoenix (MP)
System-of-Systems schemas. Given a schema, the scanner runs three
symbolic detectors that propose candidate `REJECT` rules the schema is
missing. Given an accompanying Gryphon trace file (`.gry`), it also
quantifies each candidate by counting how many traces in the file
would be eliminated by the proposed rule, with example violations.

The tool is an SME aid, not an auto-fixer. Every candidate is a
suggestion for human review.

NSA INSuRE+C, Summer 2026 — Dylan Christensen, Victor Sanchez,
Srikar Kaligotla.

## What it detects

| Shape | Signal | Description |
|------:|:-------|:------------|
| A | Vacuous-foreach gap (Signal 2) | An `ENSURE FOREACH` ordering rule passes trivially because no REJECT forces the prerequisite state to be present whenever the dependent state is active. |
| B | Symmetric REJECT completion (Signal 3, structural) | One state has a `REJECT` saying it requires a particular source set; analogous states (same root, or sharing semantic descriptor tokens across roots) do not. |
| C | Optional-event escalation (Signal 3, event-scope) | A `REJECT` is keyed off an *optional* sub-event of a state. When the optional event does not fire, the constraint is silent. Escalating the rule to the parent state closes the gap. |

For mature schemas, candidates are **implicit assumptions to confirm
with SMEs and record in the Assumption Graph**. For draft schemas,
they are **suggested REJECT rules for the schema author to triage**.

## Quick start

```bash
pip install -r requirements.txt

# CLI:
python scanner.py examples/healthcareDelivery_corrected.mp \
                  examples/healthcareDelivery_scope_1.gry

# Or with a Markdown report file:
python scanner.py examples/healthcareDelivery_corrected.mp \
                  examples/healthcareDelivery_scope_1.gry \
                  --out report.md

# Web UI:
python app.py
# then open http://localhost:5000
```

## Web UI

`app.py` exposes a single-page web interface that lets you:

- Drag-and-drop or browse for a `.mp` schema and an optional `.gry`
  trace file.
- One-click load any bundled example.
- View summary stats (roots, states, orderings, rejects, total
  findings) and per-shape candidate lists.
- For each candidate, see the rationale, the suggested `REJECT`,
  violation count and rate, and a few example violating traces.

The UI is local-only by default: it binds to `127.0.0.1:5000`, has
no auth, and is intended to be run on the analyst's own machine.

## Repository layout

```
mp-schema-scanner/
  app.py                  # Flask web app
  scanner.py              # CLI entrypoint, JSON wiring
  schema_parser.py        # parses .mp files into a Schema dataclass
  symbolic_detector.py    # Shape A/B/C detectors
  templates/index.html
  static/{style.css, app.js}
  examples/
    healthcareDelivery_corrected.mp     # canonical mature schema
    healthcareDelivery_scope_1.gry      # constrained traces (36)
    healthcareDelivery_scope_2.gry      # unconstrained traces (676)
    Smart_Home_Energy_Composed.mp       # draft SoS schema
  requirements.txt
  .gitignore
```

Larger smart-home trace files (`constrained.gry` ≈ 245 MB,
`unconstrained.gry` ≈ 800 MB) are intentionally not in version
control; point the scanner at your own local copies.

## How a `.gry` is interpreted

The parser is generic: it reads ROOT names from the schema and uses
them as keys to extract `{root_name -> state_name}` from each trace
graph in the `.gry` file. Any MP model with the same `.gry` schema
will work without code changes.

## Reading the output

```
A1. Ordering 'vitals_recorded BEFORE records_current' is vacuously
    satisfiable when ehr_up_to_date is active but device_active is
    absent. No REJECT enforces ehr_up_to_date -> (device_active).
    Suggested REJECT:
        IF #ehr_up_to_date > 0 AND #device_active == 0 THEN REJECT; FI;
    Trace evidence: 8 of 36 traces violate this proposed rule (22.2%)
        trace #3: Clinical_Device=device_recalibrating, ...
```

- **Rationale** describes the structural reason the gap was detected.
- **Suggested REJECT** is a literal MP rule that the SME can drop into
  the schema if confirmed.
- **Trace evidence** counts how many traces in the supplied `.gry`
  file the proposed rule would eliminate, plus a few examples.

## Status

Working draft. Detector tuning is calibrated against the healthcare
schema (mature; recovers known implicit #1 and #2) and the smart-home
schema (draft; surfaces 8 candidates including the
`battery_discharging`, HEMS-mode, and `demand_response_event`
patterns). Trace-evidence layer is the only feature added since the
CLI prototype.

## Roadmap

- Differential mode: compare findings between two iterations of a
  schema to track maturity.
- Statistical (lift-based) Signal 3 detector folded in as a fourth
  section.
- JSON output mode for the CLI.
- Optional packaging as a single executable for non-Python users.

## License

TBD (research artifact; internal NSA INSuRE+C use for now).
