# ATC — Co-occurrence Anomaly Flag (paper configuration)

**Model:** `ATC_System_Composed.mp` (8 ROOTs, 49 states, 28 REJECTs, 9 orderings)
**Traces:** 18,013 constrained (`atc_constrained_traces.db`)
**Criterion:** odds ratio (Haldane–Anscombe), 95% CI gate, Fisher exact, Bonferroni + BH at α=0.05

## Summary

| Family (m) | Trends | Clinging | Excluding | Bonferroni | BH |
|---:|---:|---:|---:|---:|---:|
| 542 | 91 | 49 | 42 | 53 | 70 |

## Zero-support states (structural audit)

- `center_sector_active` (ARTCC) — occurs in 0 of 18,013 traces
- `flow_normal` (Flow_Management) — occurs in 0 of 18,013 traces
- `flow_mit_applied` (Flow_Management) — occurs in 0 of 18,013 traces
- `flow_gdp_active` (Flow_Management) — occurs in 0 of 18,013 traces
- `flow_gs_active` (Flow_Management) — occurs in 0 of 18,013 traces
- `flow_afp_active` (Flow_Management) — occurs in 0 of 18,013 traces
- `flow_edct_assigned` (Flow_Management) — occurs in 0 of 18,013 traces
- `wx_vmc_conditions` (Weather_System) — occurs in 0 of 18,013 traces
- `wx_imc_conditions` (Weather_System) — occurs in 0 of 18,013 traces
- `wx_convective_sigmet` (Weather_System) — occurs in 0 of 18,013 traces
- `wx_windshear_alert` (Weather_System) — occurs in 0 of 18,013 traces
- `wx_low_visibility_ops` (Weather_System) — occurs in 0 of 18,013 traces

## Top 25 trends by |log OR|

| Pair | OR | n11 | p (Fisher) | Bonf | BH | REJECT-mentioned |
|---|---:|---:|---:|:--:|:--:|:--:|
| `center_offline` ↔ `surv_no_coverage` | 6046.93 | 973 | 0.00e+00 | ✓ | ✓ |  |
| `tracon_approach_active` ↔ `center_offline` | 0.00 | 0 | 0.00e+00 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_degraded_ssr_only` | 0.00 | 0 | 4.06e-290 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_degraded_psr_only` | 0.00 | 0 | 3.16e-264 | ✓ | ✓ |  |
| `center_flow_restricted` ↔ `surv_no_coverage` | 0.00 | 0 | 3.19e-151 | ✓ | ✓ |  |
| `center_sector_combined` ↔ `surv_no_coverage` | 0.00 | 0 | 6.76e-141 | ✓ | ✓ |  |
| `center_sector_combined` ↔ `comm_total_failure` | 0.00 | 0 | 2.03e-114 | ✓ | ✓ | ✓ |
| `ac_taxi_out` ↔ `twr_clearance_delivery` | 0.00 | 0 | 2.39e-108 | ✓ | ✓ |  |
| `ac_takeoff_roll` ↔ `surv_degraded_psr_only` | 0.00 | 0 | 6.20e-102 | ✓ | ✓ |  |
| `tracon_departure_active` ↔ `comm_total_failure` | 0.00 | 0 | 3.33e-83 | ✓ | ✓ | ✓ |
| `twr_local_control` ↔ `comm_total_failure` | 0.00 | 0 | 5.63e-77 | ✓ | ✓ |  |
| `twr_combined_position` ↔ `comm_total_failure` | 0.00 | 0 | 5.63e-77 | ✓ | ✓ | ✓ |
| `twr_clearance_delivery` ↔ `comm_total_failure` | 0.00 | 0 | 1.15e-71 | ✓ | ✓ | ✓ |
| `center_adsb_only` ↔ `surv_no_coverage` | 0.00 | 0 | 1.30e-70 | ✓ | ✓ | ✓ |
| `tracon_approach_active` ↔ `surv_no_coverage` | 0.00 | 0 | 3.36e-66 | ✓ | ✓ |  |
| `tracon_approach_active` ↔ `comm_total_failure` | 0.00 | 0 | 9.56e-54 | ✓ | ✓ | ✓ |
| `ac_takeoff_roll` ↔ `surv_no_coverage` | 0.01 | 0 | 1.53e-27 | ✓ | ✓ |  |
| `ac_holding_pattern` ↔ `tracon_offline` | 0.19 | 60 | 5.79e-55 | ✓ | ✓ |  |
| `twr_ground_control` ↔ `comm_total_failure` | 4.16 | 409 | 1.09e-79 | ✓ | ✓ |  |
| `twr_closed` ↔ `comm_total_failure` | 3.80 | 384 | 5.22e-69 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_full_coverage` | 3.19 | 1,340 | 4.31e-156 | ✓ | ✓ |  |
| `center_adsb_only` ↔ `surv_adsb_only` | 3.19 | 1,340 | 4.31e-156 | ✓ | ✓ | ✓ |
| `center_offline` ↔ `comm_total_failure` | 1.98 | 343 | 8.95e-20 | ✓ | ✓ |  |
| `tracon_combined_ops` ↔ `comm_total_failure` | 1.96 | 280 | 3.19e-17 | ✓ | ✓ |  |
| `tracon_saturated` ↔ `comm_total_failure` | 1.96 | 280 | 3.19e-17 | ✓ | ✓ |  |

Of 91 trends, **18** involve a state pair named together by a single `REJECT` rule (schema-mentioned; prime schema-induced candidates). The remaining 73 need SME adjudication.

*Note:* ordering (`ENSURE FOREACH`) vacuity is event-level and not checkable from the state DB; the zero-support audit above catches its trace-deleting form.

---

## ⚠ Data caveat (2026-07-16)

The trace export (`ATC_System_Composed_Constrained_scope_1.gry`, 2026-05-27) was
generated from a **6-ROOT** version of this model: `Flow_Management` and
`Weather_System` appear nowhere in the .gry, and their DB columns are empty.
The current `.mp` declares 8 ROOTs. The co-occurrence numbers above therefore
cover only the 6 populated components, and the 12 "zero-support" states for
Flow/Weather (plus possibly `center_sector_active`) are enumeration staleness,
not findings. **Regenerate the trace space from the current 8-ROOT model before
using these results.**
