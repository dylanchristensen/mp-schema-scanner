# ATC (8-ROOT, regenerated 2026-07-16) — Co-occurrence Anomaly Flag (paper configuration)

**Model:** `ATC_System_Composed.mp` (8 ROOTs, 49 states, 28 REJECTs, 9 orderings)
**Traces:** 350,778 constrained (`atc8.db`)
**Criterion:** odds ratio (Haldane–Anscombe), 95% CI gate, Fisher exact, Bonferroni + BH at α=0.05

## Summary

| Family (m) | Trends | Clinging | Excluding | Bonferroni | BH |
|---:|---:|---:|---:|---:|---:|
| 937 | 350 | 172 | 178 | 263 | 332 |

## Zero-support states (structural audit)

- `center_sector_active` (ARTCC) — occurs in 0 of 350,778 traces
- `flow_gdp_active` (Flow_Management) — occurs in 0 of 350,778 traces

## Top 25 trends by |log OR|

| Pair | OR | n11 | p (Fisher) | Bonf | BH | REJECT-mentioned |
|---|---:|---:|---:|:--:|:--:|:--:|
| `center_flow_restricted` ↔ `flow_mit_applied` | 127231.02 | 26,270 | 0.00e+00 | ✓ | ✓ | ✓ |
| `center_offline` ↔ `surv_no_coverage` | 121384.23 | 17,580 | 0.00e+00 | ✓ | ✓ |  |
| `tracon_approach_active` ↔ `center_offline` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_degraded_ssr_only` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_degraded_psr_only` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `twr_local_control` ↔ `flow_gs_active` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `twr_combined_position` ↔ `flow_gs_active` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `center_offline` ↔ `flow_mit_applied` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_flow_restricted` ↔ `surv_no_coverage` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_sector_combined` ↔ `flow_mit_applied` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_sector_combined` ↔ `surv_no_coverage` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_sector_combined` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `ac_taxi_out` ↔ `twr_clearance_delivery` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `ac_takeoff_roll` ↔ `surv_degraded_psr_only` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `tracon_departure_active` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `twr_clearance_delivery` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `center_adsb_only` ↔ `flow_mit_applied` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `twr_local_control` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `twr_combined_position` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `tracon_approach_active` ↔ `surv_no_coverage` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `tracon_approach_active` ↔ `comm_total_failure` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `center_adsb_only` ↔ `surv_no_coverage` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ | ✓ |
| `surv_no_coverage` ↔ `flow_mit_applied` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `ac_takeoff_roll` ↔ `surv_no_coverage` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `ac_holding_pattern` ↔ `tracon_offline` | 0.21 | 1,280 | 0.00e+00 | ✓ | ✓ |  |

Of 350 trends, **28** involve a state pair named together by a single `REJECT` rule (schema-mentioned; prime schema-induced candidates). The remaining 322 need SME adjudication.

*Note:* ordering (`ENSURE FOREACH`) vacuity is event-level and not checkable from the state DB; the zero-support audit above catches its trace-deleting form.
