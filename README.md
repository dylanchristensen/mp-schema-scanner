# MP Schema Gap Scanner

A small tool for finding missing assumptions in Monterey Phoenix (MP)
System-of-Systems schemas. Given a schema, the scanner runs three
symbolic detectors that propose candidate `REJECT` rules the schema is
missing. Given an accompanying Gryphon trace file (`.gry`), it also
quantifies each candidate by counting how many traces in the file
would be eliminated by the proposed rule, with example violations.

The tool is an SME aid, not an auto-fixer. Every candidate is a
suggestion for human review.

NSA INSuRE+C, Summer 2026. Dylan Christensen, Victor Sanchez,
Srikar Kaligotla.

## How It Works

At a high level, the scanner bridges the gap between raw execution data and architectural intent:

1. **Input Generation**: A system architect writes an MP model (`.mp` file) defining the components, states, and rules of a System of Systems. Monterey Phoenix then compiles this model and exhaustively generates a set of **execution traces** (`.gry` files), which represent every physically and logically possible sequence of events.
2. **Automated Scanning**: The `mp-schema-scanner` parses these traces and scans them against predefined heuristic patterns. 
3. **Anomaly Flagging**: When a trace matches a problematic pattern, the scanner flags it as a "Candidate Finding" and presents it to the researcher for adjudication.
4. **Rule Proposal**: For certain anomalies, the scanner automatically synthesizes and proposes new MP `REJECT` rules that the architect could add to the model to forbid the unintended behavior.

## Detection Flags and Implementation Patterns

The paper defines three overarching **Flags** used to score traces: the Explicit-violation flag, the Vacuous-satisfaction flag, and the Co-occurrence anomaly flag.

Under the hood, the scanner implements these theoretical flags by searching for specific mathematical anti-patterns in the schema's logic:

- **Flag: Vacuous-satisfaction (Pattern A: vacuous-foreach gaps)**: This occurs when an MP rule enforces an ordering condition between two events, but the model designer forgot to mandate that the prerequisite event must actually exist. If it never happens, the "BEFORE" condition evaluates to *vacuously true*.
- **Schema check (Pattern B: symmetric REJECT completion)**: a `REJECT` rule is present for one state but missing for an analogous sibling state. This is a schema-level check with no trace-space counterpart; it is not the co-occurrence flag.
- **Schema check (Pattern C: optional-event escalation)**: a `REJECT` rule is keyed on an optional sub-event when it should escalate to the parent state. Also schema-level only.

The co-occurrence anomaly flag is statistical and lives in `pipeline/run_cooccurrence_pipeline.py` (see "Pipeline, models, and reports" below). The scanner itself does not compute it.

## The AI Subject Matter Expert (SME) Integration

Identifying an anomaly in a trace is only half the battle. The harder part is determining *why* the anomaly exists. To solve this, the scanner integrates with an **AI SME** (powered by OpenRouter). When a trace is flagged, the researcher can pass the trace and the domain context to the LLM. The tool ships without a key: enter an OpenRouter key in the key box at the top of the UI, or set the `OPENROUTER_API_KEY` environment variable before launching. The default model in the dropdown is a free-tier one.

The AI SME acts as a senior systems architect and classifies the anomaly into exactly one of three categories:

1. **Modeling Gap**: The trace represents a physical impossibility. The designer simply forgot to write a rule forbidding it. (Action: Accept the scanner's proposed `REJECT` rule).
2. **Missing Assumption**: The trace is physically possible, but violates an undocumented trust assumption between two separate components. (Action: Document an "Implicit Assumption Edge").
3. **Genuine Emergent Behavior**: The trace is fully valid, utilizes no broken assumptions, but still results in a systemic failure. This is a true **Weird Machine**. (Action: Document the sequence of logical "gadgets" that form the exploit).

## Statistical and Logical Formalisms (The Math)

The scanner isn't just looking for simple text strings; it relies on formal logic and statistical testing to flag anomalies. 

### Vacuous Satisfaction (Pattern A)
This relies on formal boolean logic. An MP ordering rule is formatted as a universal quantification:
$\forall x \in \text{traces}, (A \implies B)$

In logic, a material implication $A \implies B$ is **vacuously true** if the antecedent ($A$) is false. Therefore, if the prerequisite event $A$ simply never occurs in the trace, the rule evaluates to `True`, and the trace passes validation. The scanner formally checks the AST (Abstract Syntax Tree) of the schema to ensure that every `BEFORE` clause is accompanied by a strict `REJECT` rule that enforces the existence of the antecedent.

### Symmetric completion and optional-event escalation (Patterns B & C)
Both are purely structural. Pattern B starts from each existing `REJECT` of the form "X requires Y" and looks for states analogous to X (siblings in the same `ROOT` that share a descriptor token or a source/sink role, or states in other `ROOT`s that share a non-passive name token) that have no `REJECT` requiring Y; each is proposed as a candidate for the analogous rule. Pattern C starts from each `REJECT` whose antecedent is an optional event `[e]` of some state X. Such a rule only fires when the optional event happens to occur, so if the intent is "X always requires Y" the rule should be escalated to X itself; the detector flags cases where no parent-state-level counterpart exists. Neither touches trace data; both propose a candidate `REJECT` clause for SME review.

### Co-occurrence Anomaly (`pipeline/run_cooccurrence_pipeline.py`)
To detect unwritten dependencies (missing assumptions) between two states $X$ and $Y$ in different components, the co-occurrence pipeline builds a $2 \times 2$ contingency table across the entire generated trace space. It then runs rigorous statistical tests to determine if the states appear together more or less than random chance would predict:

1. **Odds Ratio (OR)**: Computes the association strength.
   `OR = (X_and_Y * notX_and_notY) / (X_and_notY * notX_and_Y)`
   To prevent division by zero, the **Haldane--Anscombe correction** adds $0.5$ to every cell in the contingency table.
2. **Log Odds Ratio**: Inference runs on $\log(\text{OR})$ to ensure symmetric scaling about independence (zero). The scanner uses a $95\%$ confidence interval on the $\log(\text{OR})$ as a gate. Surviving trends are ranked by $|\log \text{OR}|$.
3. **Fisher's Exact Test**: Because individual state pairs may produce sparse tables, the scanner uses Fisher's exact test on the uncorrected table to compute the exact probability of an association at least as extreme under the null hypothesis (independence).
4. **Multiple-Testing Corrections**: Since hundreds of state pairs are tested simultaneously, the scanner applies family-wise error rate corrections:
   - **Bonferroni**: A conservative bound that divides the threshold by the total number of tests to strictly control false positives.
   - **Benjamini--Hochberg (FDR)**: Controls the false discovery rate, adapting the threshold to the rank order of the $p$-values. This is the primary operative algorithm used for large trace spaces.

## Quick start

### Option A -- standalone Windows binary (recommended for end users)

No Python needed. Grab `mp-scanner-iag.exe` from the latest build (or
build it yourself, see below), double-click it. A console window
appears with the URL it is serving on; your default browser opens to
the UI automatically.

To include your own schemas/traces in the **Examples** list, create
an `examples\` folder *next to* `mp-scanner-iag.exe` and drop `.mp` and
`.gry` files in there. Bundled examples remain available; same-named
files beside the exe win.

### Option B -- Python source

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
# (auto-opens browser to a free port, usually http://127.0.0.1:5000)
```

### Building the standalone binary

```powershell
# Windows PowerShell, from the repo root:
pip install -r requirements-dev.txt
.\build.ps1
# -> dist\mp-scanner-iag.exe  (~23 MB, single file)
```

The build pulls in Flask, waitress, and the project's modules with
PyInstaller's `--onefile` mode (configured via `mp-scanner.spec`).

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
  app.py                  # Flask web app + standalone launcher
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
  pipeline/               # enumerator, .gry parser, co-occurrence flag, run_model
  analysis/               # exploratory scripts; legacy/ has the spring per-model parsers
  models/                 # all nine MP schemas in the study + README of counts
  reports/                # per-model pipeline, co-occurrence and scan reports
  docs/                   # model write-ups and pipeline notes
  requirements-analysis.txt  # adds scipy for analysis/differential_*.py
  mp-scanner.spec         # PyInstaller bundle config
  build.ps1               # one-shot build script
  requirements.txt
  requirements-dev.txt
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
- GitHub Actions release workflow that builds the .exe on tag push
  and attaches it to a release, so teammates can grab the binary
  without ever cloning the repo.

## License

TBD (research artifact; internal NSA INSuRE+C use for now).

## Pipeline, models, and reports

Everything below was added after the scanner's initial release. The scanner
modules (`schema_parser.py`, `symbolic_detector.py`, `scanner.py`,
`assumption_graph.py`, `app.py`) stay at the repo root; the new folders import
them by relative path, so run every command from the repo root.

```
pipeline/
  mp_enumerate.py              closed-form MP enumerator (stdlib only). Reproduces
                               Gryphon's constrained trace counts exactly on every
                               model in models/. Optional second arg writes a SQLite
                               trace database in the same layout gry_parse.py produces.
  gry_parse.py                 Gryphon .gry  ->  SQLite (one row per trace, one
                               column per ROOT). Reads ROOT names from the schema.
  run_cooccurrence_pipeline.py the co-occurrence anomaly flag, paper configuration:
                               2x2 table per cross-component pair, Haldane-Anscombe
                               odds ratio, 95% CI gate, Fisher's exact test,
                               Bonferroni + Benjamini-Hochberg. Needs numpy.
  run_model.py                 one-shot pass over a model + trace DB: schema scan with
                               trace evidence, lift ranking, dead-state check.
  explore_lift.py              lift-based ranking (an earlier measure; kept because
                               run_model.py and the spring reports use it).
analysis/                      exploratory and one-off scripts used in the reports
  reduce2.py                   collapses flagged traces to distinct review patterns
  iag_dot.py                   renders the assumption graph of a schema to Graphviz .dot
  differential_*.py            unconstrained-vs-constrained z-tests (needs scipy)
  legacy/                      per-model parsers from the spring, superseded by gry_parse.py
models/                        every MP schema in the study, with a README of counts
reports/                       per-model pipeline, co-occurrence, and scan reports
docs/                          model write-ups and pipeline notes
```

### Reproducing the paper's numbers

```bash
pip install -r requirements.txt          # Flask, waitress, openai, numpy

# 1. Enumerate a model (prints unconstrained/constrained counts as JSON).
python pipeline/mp_enumerate.py models/healthcareDelivery_corrected.mp
#   -> {"unconstrained": 729, "constrained": 36, ...}

# 2. Enumerate straight into a trace database (no Gryphon needed) ...
python pipeline/mp_enumerate.py models/Smart_Home_Energy_Composed.mp smart_home.db

#    ... or load a Gryphon .gry you already have.
python pipeline/gry_parse.py models/Smart_Home_Energy_Composed.mp constrained.gry smart_home.db

# 3. Run the co-occurrence flag. Writes a Markdown report and prints the summary.
python pipeline/run_cooccurrence_pipeline.py models/Smart_Home_Energy_Composed.mp smart_home.db report.md smart_home
#   -> {"N": 18080, "m": 384, "trends": 153, "cling": 79, "excl": 74, "bonf": 118, "bh": 142}

# 4. Scanner + lift + dead-state pass in one go.
python pipeline/run_model.py models/Smart_Home_Energy_Composed.mp smart_home.db

# 5. Collapse flagged traces to review patterns; draw the assumption graph.
python analysis/reduce2.py models/Smart_Home_Energy_Composed.mp smart_home.db
python analysis/iag_dot.py models/Smart_Home_Energy_Composed.mp smart_home.dot && dot -Tpng smart_home.dot -o smart_home.png
```

Verified on 2026-09-25 from a clean checkout: every model in `models/` enumerates
to the count in `models/README.txt`, and step 3 on the smart home reproduces
384 / 153 / 118 / 142.

### What is deliberately not in the repo

Trace files (`.gry`, up to about 1 GB) and the SQLite databases they parse into.
`.gitignore` already excludes them. Regenerate with `mp_enumerate.py` or
`gry_parse.py`. The packaged Windows binary (`dist/mp-scanner-iag.exe`, about 23 MB)
is also ignored; attach it to a GitHub release instead of committing it.

## Assumption Graph

The scanner also builds the Implicit Assumption Graph (explicit edges from
the schema + implicit edges discovered by the SME agent over flagged trace
patterns). See `ASSUMPTION_GRAPH.md` for the design and process.
