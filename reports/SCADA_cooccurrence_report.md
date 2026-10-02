# Power-Grid SCADA — Co-occurrence Anomaly Flag (paper configuration)

**Model:** `Power_Grid_SCADA_Composed.mp` (8 ROOTs, 31 states, 9 REJECTs, 4 orderings)
**Traces:** 14,733 constrained (`scada_constrained_traces.db`)
**Criterion:** odds ratio (Haldane–Anscombe), 95% CI gate, Fisher exact, Bonferroni + BH at α=0.05

## Summary

| Family (m) | Trends | Clinging | Excluding | Bonferroni | BH |
|---:|---:|---:|---:|---:|---:|
| 393 | 107 | 61 | 46 | 65 | 93 |

## Zero-support states (structural audit)

- `breaker_open` (Substation_Breaker) — occurs in 0 of 14,733 traces

## Top 25 trends by |log OR|

| Pair | OR | n11 | p (Fisher) | Bonf | BH | REJECT-mentioned |
|---|---:|---:|---:|:--:|:--:|:--:|
| `dist_feeder_fault` ↔ `ami_blackout_detected` | 7656.45 | 1,161 | 0.00e+00 | ✓ | ✓ | ✓ |
| `scada_blind` ↔ `ot_net_partitioned` | 6835.77 | 1,533 | 0.00e+00 | ✓ | ✓ | ✓ |
| `ems_load_shedding` ↔ `ami_disconnect_active` | 6306.67 | 936 | 0.00e+00 | ✓ | ✓ | ✓ |
| `line_nominal` ↔ `microgrid_islanded` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `breaker_opening` ↔ `line_faulted` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `ems_nominal` ↔ `ot_net_partitioned` | 0.00 | 0 | 1.61e-231 | ✓ | ✓ |  |
| `ems_agc_active` ↔ `ot_net_partitioned` | 0.00 | 0 | 1.61e-231 | ✓ | ✓ |  |
| `ied_issuing_goose_trip` ↔ `ot_net_partitioned` | 0.00 | 0 | 4.35e-180 | ✓ | ✓ | ✓ |
| `dist_feeder_fault` ↔ `ami_disconnect_active` | 0.00 | 0 | 5.45e-173 | ✓ | ✓ |  |
| `ems_load_shedding` ↔ `ami_blackout_detected` | 0.00 | 0 | 3.36e-147 | ✓ | ✓ |  |
| `dist_feeder_fault` ↔ `ami_reporting` | 0.00 | 0 | 5.45e-128 | ✓ | ✓ |  |
| `dist_feeder_fault` ↔ `ami_demand_response` | 0.00 | 0 | 5.45e-128 | ✓ | ✓ |  |
| `ems_load_shedding` ↔ `ami_reporting` | 0.00 | 0 | 2.80e-102 | ✓ | ✓ |  |
| `ems_load_shedding` ↔ `ami_demand_response` | 0.00 | 0 | 2.80e-102 | ✓ | ✓ |  |
| `ems_load_shedding` ↔ `ot_net_partitioned` | 0.00 | 0 | 1.11e-46 | ✓ | ✓ |  |
| `ems_load_shedding` ↔ `dist_feeder_fault` | 0.01 | 0 | 6.63e-35 | ✓ | ✓ |  |
| `breaker_closed` ↔ `line_faulted` | 2.67 | 1,500 | 6.18e-112 | ✓ | ✓ |  |
| `baseload_running` ↔ `line_faulted` | 0.50 | 375 | 8.84e-35 | ✓ | ✓ | ✓ |
| `line_nominal` ↔ `dist_nominal` | 1.81 | 1,392 | 3.37e-46 | ✓ | ✓ |  |
| `line_nominal` ↔ `dist_peak_load` | 1.81 | 1,392 | 3.37e-46 | ✓ | ✓ |  |
| `scada_blind` ↔ `ot_net_nominal` | 0.57 | 2,044 | 3.09e-59 | ✓ | ✓ |  |
| `scada_blind` ↔ `ot_net_congested` | 0.57 | 2,044 | 3.09e-59 | ✓ | ✓ |  |
| `line_overloaded` ↔ `microgrid_islanded` | 1.63 | 1,392 | 2.03e-33 | ✓ | ✓ |  |
| `line_de_energized` ↔ `microgrid_islanded` | 1.63 | 1,392 | 2.03e-33 | ✓ | ✓ |  |
| `dist_nominal` ↔ `ami_blackout_detected` | 0.63 | 1,161 | 1.94e-31 | ✓ | ✓ |  |

Of 107 trends, **9** involve a state pair named together by a single `REJECT` rule (schema-mentioned; prime schema-induced candidates). The remaining 98 need SME adjudication.

*Note:* ordering (`ENSURE FOREACH`) vacuity is event-level and not checkable from the state DB; the zero-support audit above catches its trace-deleting form.
