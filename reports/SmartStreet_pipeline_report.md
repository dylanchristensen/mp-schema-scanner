# Connected Street / V2X — Pipeline Run

**Model:** `Connected_Street_V2X_Composed.mp` (8 ROOTs, 32 states, 6 orderings, 12 REJECTs)
**Trace space:** 24,536 traces (`..._Constrained_scope_1.gry`, 665 MB)
**Run date:** 2026-06-21 · Pipeline: symbolic scan + Direction A lift (constrained-only). All 8 ROOTs present.

## ⚠️ Safety-critical structural finding
**`av_braking_emergency` is unreachable — 0 of 24,536 traces.** The
autonomous-vehicle emergency-braking state never fires in any trace. As with
SCADA's `breaker_open`, this is the transition-as-presence-state trap: a REJECT
plus MP's one-state-per-ROOT semantics makes the state impossible. For a safety
model this is the most important thing to fix — emergency braking should be
reachable.

## Direction A — top implicit candidates (lift)
826 cross-ROOT pairs → 814 implicit after removing 6 forced + 6 mutex.

| Rank | Pair | lift | conf | read |
|---:|---|---:|---:|---|
| 1–4 | `av_cruising` ↔ `object_detected` / `perception_clear` | 1.84 | 50% | **safety-relevant** — AV cruising while an object is detected |
| 5–8 | `mec_hazard_broadcasting` ↔ `ev_on_scene` / `ev_inactive` | 1.61 | — | edge-server hazard broadcast vs emergency-vehicle state |
| 9–14 | `phase_green` ↔ `tc_preempt_active` / `tc_coord_normal` / `tc_transit_priority` | 1.32 | — | signal-phase vs controller-mode structure |
| 15 | `av_cruising` ↔ `vru_in_roadway` | 1.24 | — | AV cruising with a vulnerable road user present |

The `av_cruising ↔ object_detected` and `av_cruising ↔ vru_in_roadway` pairs are the safety-interesting candidates — the vehicle in a normal-cruise state while a hazard is present.

## Symbolic scanner — 7 candidates (all Shape B)

| Suggested REJECT (informal) | Cut | % | note |
|---|---:|---:|---|
| `av_braking_normal` requires `collision_predicted` | 5,592 | 22.8% | braking without a predicted collision — over-fire (normal braking ≠ collision) |
| `tc_coord_normal` / `tc_transit_priority` requires `ev_responding` | 5,572 | 22.7% | over-fire of the `ev_responding` symmetric completion |
| `overlap_active` requires `ev_responding` | 4,296 | 17.5% | over-fire |
| `tc_flash_fault` requires `ev_responding` | 4,140 | 16.9% | over-fire |
| `vru_crossing_active` requires `ev_responding` | 3,852 | 15.7% | over-fire |
| `obu_tx_rx_active` requires `ev_responding` | 3,694 | 15.1% | over-fire |

The Shape-B group here is almost entirely the `ev_responding` analogy over-firing across unrelated states — dismissable. The real signal is structural (`av_braking_emergency` unreachable) plus the Direction-A cruise-with-hazard pairs.

## Bottom line
Fix the unreachable `av_braking_emergency` state first. Then the
`av_cruising ↔ object_detected` / `vru_in_roadway` pairs are the candidates for
the SME tool.
