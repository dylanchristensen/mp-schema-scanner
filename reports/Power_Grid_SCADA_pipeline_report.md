# Power Grid / SCADA — Pipeline Run

**Model:** `Power_Grid_SCADA_Composed.mp` (8 ROOTs, 31 states, 4 orderings, 9 REJECTs, 4 COORDINATE blocks)
**Constrained trace space:** 14,733 traces (`Power_Grid_SCADA_Composed_scope_1.gry`, 335 MB)
**Run date:** 2026-06-21 · NSA INSuRE+C Summer 2026
**Pipeline:** symbolic gap scan + Direction A (single-set lift) on the constrained set. *No unconstrained / differential analysis (dropped).*

> Trace-level SME adjudication is handled separately with your own tool; this
> report surfaces the candidates and structural observations to feed it.

---

## Headline candidates

1. **`line_faulted` + `breaker_closed`** (Direction A: lift 1.52, conf 57%, 1,500 traces / 10.2%).
   A faulted line with the breaker still closed — the fault is **not being
   cleared**. Nothing in the schema forbids it, so it is a genuine
   permitted-but-unintended composition (protection-failure / latent-trip).
   Top of the lift ranking and *not* schema-induced.
2. **GOOSE trip without a detected fault** (scanner A1: 3,300 traces / 22.4%).
   The relay can be in `ied_issuing_goose_trip` while never in
   `ied_overcurrent_detected` — a trip command with no protection pickup
   behind it. This is the classic spoofed/false-trip SCADA weird-machine and
   is security-relevant.
3. **Spurious breaker operation** (scanner A2: 4,036 traces / 27.4%).
   `breaker_opening` with no `line_faulted` present — the breaker mechanism
   operates without a fault to clear.

## Structural artifact found while parsing

**`breaker_open` is unreachable — 0 of 14,733 traces.** REJECT #3
(`breaker_open` requires `breaker_opening`) combined with MP's one-state-per-ROOT
semantics makes it impossible: a trace can hold either `breaker_open` or
`breaker_opening`, never both, so `breaker_open` is always rejected. The
intended transition sequence (`opening → open`) can't be expressed as two
presence-states of one ROOT. Likely a modeling bug to fix before further runs.

---

## Layer 1 — Symbolic gap scanner (schema-only)

9 candidates (2 Shape A, 7 Shape B, 0 Shape C), each quantified against the
14,733-trace space.

| ID | Proposed REJECT (informal) | Traces cut | % | Note |
|----|----------------------------|-----------:|----:|------|
| **A1** | `ied_issuing_goose_trip` requires `ied_overcurrent_detected` | 3,300 | 22.4% | Trip with no detected fault (same-ROOT vacuity → all goose-trip traces). High security relevance. |
| **A2** | `breaker_opening` requires `line_faulted` | 4,036 | 27.4% | Breaker operates with no fault present. |
| B6 | `ot_net_congested` requires `scada_blind` | 4,556 | 30.9% | Over-fire: congestion ≠ partition; SCADA isn't necessarily blind. |
| B7 | `ot_net_nominal` requires `scada_blind` | 4,556 | 30.9% | Clear false positive (nominal net, blind SCADA makes no sense). |
| B2 | `dist_nominal` requires `ami_blackout_detected` | 3,827 | 26.0% | Clear false positive (nominal feeders, no blackout). |
| B3 | `dist_peak_load` requires `ami_blackout_detected` | 3,827 | 26.0% | False positive. |
| B1 | `dist_peak_load` requires `ami_disconnect_active` | 3,483 | 23.6% | Over-fire of the load-shed analogy. |
| B4 | `ems_agc_active` requires `ami_disconnect_active` | 3,152 | 21.4% | Over-fire (only `ems_load_shedding` needs disconnects). |
| B5 | `ems_nominal` requires `ami_disconnect_active` | 3,152 | 21.4% | Over-fire. |

The Shape-B group mostly over-fires here: the symmetric-completion heuristic
projects each "X requires Y" rule onto X's same-ROOT siblings, but the
asymmetry is intentional (only `ot_net_partitioned` blinds SCADA; only
`dist_feeder_fault` triggers blackout; only `ems_load_shedding` disconnects).
A1/A2 are the candidates worth feeding to the SME tool.

---

## Layer 2 — Direction A (single-set lift)

760 cross-ROOT ordered pairs → 754 implicit candidates after removing 6
REJECT-forced pairs, ranked by lift. Top of the ranking:

| Rank | Pair | lift | conf | read |
|---:|---|---:|---:|---|
| 1–2 | `line_faulted` ↔ `breaker_closed` | 1.52 | 57% | **genuine** — fault not cleared (see headline) |
| 3–8 | `line_nominal` ↔ dist states | 1.32 | — | cross-layer structure; mostly benign |
| 9–14 | IED states ↔ `ot_net_partitioned` | 1.29 | — | schema-induced: the no-GOOSE-on-partition mutex pushes mass onto the other IED states |
| 15–20 | `microgrid_islanded` ↔ non-nominal line | 1.27 | — | schema-induced by the islanding REJECT (island only when line ≠ nominal) |
| 21–22 | `line_faulted` ↔ `breaker_failure_to_trip` | 1.22 | — | cascade REJECTs |

Same scaling pattern as smart home: once the obviously schema-induced pairs
(partition mutex, islanding rule, cascade rules) are recognized, only the
**`line_faulted` ↔ `breaker_closed`** pair stands out as a genuine candidate.
The lift ranking on its own does not separate these — the hubs here are
`ot_net_partitioned` and the line-state cascade.

---

## What this adds to the scaling story

- A second constraint-rich model (8 ROOTs vs smart home's 7) reproduces the
  pattern: **statistical lift is dominated by schema-induced structure;
  the symbolic scanner yields the cleaner, security-relevant candidates** (the
  false-GOOSE-trip and spurious-breaker cases).
- SCADA adds something smart home didn't: a **genuine unreachable-state bug**
  (`breaker_open`) and a **headline weird-machine** (faulted line + closed
  breaker) that maps directly onto a real grid-protection failure.
- Candidates to push into your SME trace tool: **A1** (false GOOSE trip),
  **A2** (spurious breaker), and the Direction-A **`line_faulted`+`breaker_closed`**
  set. The Shape-B group can mostly be dismissed as justified asymmetries.

## Appendix — reproduction
- Parse: `parse_scada.py` → `scada_constrained_traces.db` (8-col, 14,733 rows).
- Symbolic scan: `python scanner.py Power_Grid_SCADA_Composed.mp`
- Direction A: `python run_scada_lift.py` (forced/mutex pairs derived from the 9 REJECTs).
- State labels stored space-separated (e.g. `line faulted`).
