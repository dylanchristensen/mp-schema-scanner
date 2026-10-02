# Smart Street V2X — Co-occurrence Anomaly Flag (paper configuration)

**Model:** `Connected_Street_V2X_Composed.mp` (8 ROOTs, 32 states, 12 REJECTs, 6 orderings)
**Traces:** 24,536 constrained (`smartstreet_constrained_traces.db`)
**Criterion:** odds ratio (Haldane–Anscombe), 95% CI gate, Fisher exact, Bonferroni + BH at α=0.05

## Summary

| Family (m) | Trends | Clinging | Excluding | Bonferroni | BH |
|---:|---:|---:|---:|---:|---:|
| 420 | 160 | 82 | 78 | 93 | 137 |

## Zero-support states (structural audit)

- `av_braking_emergency` (AV_Kinematics) — occurs in 0 of 24,536 traces

## Top 25 trends by |log OR|

| Pair | OR | n11 | p (Fisher) | Bonf | BH | REJECT-mentioned |
|---|---:|---:|---:|:--:|:--:|:--:|
| `tc_preempt_active` ↔ `ev_responding` | 11146.94 | 2,472 | 0.00e+00 | ✓ | ✓ | ✓ |
| `phase_green` ↔ `tc_flash_fault` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `tc_preempt_active` ↔ `ev_inactive` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `tc_preempt_active` ↔ `ev_on_scene` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `ev_responding` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `av_cruising` ↔ `collision_predicted` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `av_cruising` ↔ `sensor_degraded` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `tc_preempt_active` ↔ `mec_hazard_broadcasting` | 0.00 | 0 | 4.02e-83 | ✓ | ✓ |  |
| `collision_predicted` ↔ `mec_hazard_broadcasting` | 4.81 | 990 | 1.99e-204 | ✓ | ✓ | ✓ |
| `mec_hazard_broadcasting` ↔ `vru_in_roadway` | 4.53 | 932 | 1.36e-186 | ✓ | ✓ | ✓ |
| `av_accelerating` ↔ `vru_in_roadway` | 0.25 | 532 | 2.78e-239 | ✓ | ✓ | ✓ |
| `av_cruising` ↔ `phase_red` | 0.25 | 252 | 7.77e-129 | ✓ | ✓ | ✓ |
| `av_cruising` ↔ `perception_clear` | 3.15 | 1,486 | 2.63e-176 | ✓ | ✓ |  |
| `av_cruising` ↔ `object_detected` | 3.15 | 1,486 | 2.63e-176 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `ev_inactive` | 2.36 | 862 | 4.05e-64 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `ev_on_scene` | 2.36 | 862 | 4.05e-64 | ✓ | ✓ |  |
| `sensor_degraded` ↔ `mec_hazard_broadcasting` | 0.46 | 198 | 1.63e-27 | ✓ | ✓ |  |
| `perception_clear` ↔ `mec_hazard_broadcasting` | 0.47 | 268 | 1.63e-32 | ✓ | ✓ |  |
| `object_detected` ↔ `mec_hazard_broadcasting` | 0.47 | 268 | 1.63e-32 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `vru_safe_distance` | 0.50 | 264 | 7.54e-27 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `vru_crossing_active` | 0.50 | 264 | 7.54e-27 | ✓ | ✓ |  |
| `mec_hazard_broadcasting` ↔ `vru_device_offline` | 0.50 | 264 | 7.54e-27 | ✓ | ✓ |  |
| `phase_green` ↔ `tc_coord_normal` | 1.76 | 2,068 | 7.08e-65 | ✓ | ✓ |  |
| `phase_green` ↔ `tc_transit_priority` | 1.76 | 2,068 | 7.08e-65 | ✓ | ✓ |  |
| `av_cruising` ↔ `mec_hazard_broadcasting` | 0.63 | 140 | 4.03e-08 | ✓ | ✓ |  |

Of 160 trends, **16** involve a state pair named together by a single `REJECT` rule (schema-mentioned; prime schema-induced candidates). The remaining 144 need SME adjudication.

*Note:* ordering (`ENSURE FOREACH`) vacuity is event-level and not checkable from the state DB; the zero-support audit above catches its trace-deleting form.
