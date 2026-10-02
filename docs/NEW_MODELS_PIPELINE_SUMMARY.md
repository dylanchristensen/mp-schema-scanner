# Three New Models Through the CHIMERA Co-occurrence Flag — 2026-07-16

Pipeline: `run_cooccurrence_pipeline.py` — the paper's Section-4 configuration
(odds ratio with Haldane–Anscombe correction, 95% CI gate → trends, Fisher's
exact test, Bonferroni + Benjamini–Hochberg at α=0.05, family = cross-component
state pairs with support > 0), plus the zero-support structural audit.

**Validation:** run first on the smart-home model; reproduces the paper's
published numbers *exactly* (m=384, 153 trends = 79 clinging + 74 excluding,
118 Bonferroni, 142 BH survivors). The published smart-home Table-2/3 numbers
are therefore now independently reproducible from the raw trace DB in this repo.

## Results (Table-2/3 format)

| Model | ROOTs | Constrained traces | Family m | Trends (cling/excl) | Bonferroni | BH |
|---|---:|---:|---:|---|---:|---:|
| Smart-home (validation) | 7 | 18,080 | 384 | 153 (79/74) | 118 | 142 |
| Power-Grid SCADA | 8 | 14,733 | 393 | 107 (61/46) | 65 | 93 |
| Smart Street V2X | 8 | 24,536 | 420 | 160 (82/78) | 93 | 137 |
| ATC ⚠ | 8 (6 in data) | 18,013 | 542 | 91 (49/42) | 53 | 70 |

⚠ ATC: the .gry/DB were generated from an older **6-ROOT** model —
`Flow_Management` and `Weather_System` have never been enumerated. Regenerate
before use (see caveat in `ATC/ATC_cooccurrence_report.md`).

## Headline structural findings (zero-support audit)

Both clean models contain a **dead safety-critical state** — the same
rule-composition suppression the paper reports for smart-home DR shedding and
maritime cargo ops, here on protection/safety functions:

### SCADA: `breaker_open` never occurs (0 of 14,733)
Mechanism = the maritime cargo-ops bug. The rule
`IF #breaker_open > 0 AND #breaker_opening == 0 THEN REJECT`
requires `breaker_open` to co-occur with `breaker_opening` — a **mutually
exclusive sibling** in the `Substation_Breaker` alternation. Self-contradictory;
the breaker can never reach the open state. The protection outcome the model
exists to represent is unreachable.

### Smart Street: `av_braking_emergency` never occurs (0 of 24,536)
Mechanism = the smart-home DR-shedding bug, on AEB. Two individually reasonable
rules compose fatally:
1. `IF #av_braking_emergency > 0 AND #collision_predicted == 0 THEN REJECT`
   (AEB requires a collision prediction) — forces the pair together.
2. `ENSURE FOREACH ttc_below_threshold BEFORE aeb_activated` — the two events
   belong to uncoordinated ROOTs (`AV_Compute` vs `AV_Kinematics`), so the
   ordering deletes every trace in which both occur.

Rule 1 mandates the co-occurrence; rule 2 deletes it. Emergency braking is
impossible in the model: verified — all 5,985 `collision_predicted` traces have
kinematics ∈ {accelerating, braking normal, stopped}.

## Per-model reports

- `SCADA/SCADA_cooccurrence_report.md`
- `Smart Street/SmartStreet_cooccurrence_report.md`
- `ATC/ATC_cooccurrence_report.md` (with staleness caveat)

## Suggested next steps

1. Regenerate the ATC trace space from the current 8-ROOT `.mp` and rerun.
2. SME adjudication of the SCADA (107) and Smart Street (160) trend sets —
   reports pre-mark pairs named together by a single REJECT (schema-mentioned).
3. The two dead-state mechanisms are strong candidates for the paper's
   Sections 7–8 arc: they reproduce both published suppression mechanisms on
   new domains, including one on a life-safety function (AEB).

---

# UPDATE 2026-07-16: ATC regenerated at 8 ROOTs (`mp_enumerate.py`)

The stale 6-ROOT trace data is superseded. `mp_enumerate.py` implements the
closed-form MP semantics and reproduces the MP ground truth **exactly** on all
three reference models (healthcare 729→36, smart-home 57,600→18,080, maritime
172,800→45,836) before use here.

## ATC, current 8-ROOT model

| | |
|---|---:|
| Unconstrained traces | 1,312,500 |
| Constrained traces (28 REJECTs, 9 orderings) | **350,778** |
| Family m | 937 |
| Trends (clinging / excluding) | 350 (172 / 178) |
| Bonferroni / BH survivors | 263 / 332 |

Largest trace space in the study by ~9×; detection-power scaling holds.
DB: `ATC/atc_8root_constrained_traces.db`; report: `ATC/ATC_cooccurrence_report_8root.md`.

## ATC structural findings — including a THIRD suppression mechanism

**1. `center_sector_active` is dead (0 of 350,778).** The ENSURE
"conflict detection BEFORE flight-level changes" (FAA 7110.65 §5-8) contradicts
the state's own event grammar, which lists `issuing_flight_level_changes`
*before* `conflict_detection_active`. Every trace containing the state violates
the ordering and is deleted. This is a **within-state grammar-order/ENSURE
contradiction** — distinct from both published mechanisms (sibling-REJECT
self-contradiction; cross-ROOT ordering deletion). The ARTCC's primary
operating state — a normally staffed en-route sector — cannot exist in the model.

**2. `flow_gdp_active` is dead (0 of 350,778).** Same mechanism: the ENSURE
"EDCT computed BEFORE ground delay program" vs. the state grammar listing
`ground_delay_program` first. Ground delay programs are impossible.

**3. The standard IFR departure sequence is impossible.** The cross-ROOT
ordering `issuing_ifr_clearance BEFORE squawk_assigned` (ICAO 4444 §4.5) spans
Tower_Control and Aircraft, which nothing coordinates — so it deletes every
trace pairing `twr_clearance_delivery` with `ac_taxi_out` (verified: 0 such
traces). Clearance delivery and taxi-out can never co-occur: the DR-shedding
mechanism, on the nominal departure workflow.

Mechanism census across the five models:
| Mechanism | Instances |
|---|---|
| Sibling-REJECT self-contradiction | maritime `cargo_ops_active`, SCADA `breaker_open` |
| Cross-ROOT ordering deletion | smart-home DR shedding, Smart Street AEB, ATC departure sequence |
| Within-state grammar/ENSURE contradiction (new) | ATC `center_sector_active`, ATC `flow_gdp_active` |
