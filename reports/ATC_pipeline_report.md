# Air Traffic Control (ATC) — Pipeline Run

**Model:** `ATC_System_Composed.mp` (8 ROOTs, 49 states, 9 orderings, 28 REJECTs)
**Trace space:** 18,013 traces (`ATC_System_Composed_Constrained_scope_1.gry`, 387 MB)
**Run date:** 2026-06-21 · Pipeline: symbolic scan + Direction A lift (constrained-only).

> ## ⚠️ Data/model mismatch — read first
> The trace file contains **only 6 of the 8 ROOTs**. `Flow_Management` and
> `Weather_System` are **entirely absent** — the `.gry` was generated from a
> reduced model that does not match the 8-ROOT schema. Every flow/weather
> REJECT and ordering is therefore un-exercised, and ~half the scanner's
> Shape-B candidates trip only because a required weather/flow state can never
> be present. **Regenerate the trace space from the full 8-ROOT model before
> trusting any ATC result below.**

## Direction A — top implicit candidates (lift)
1,052 cross-ROOT pairs → 1,020 implicit after removing 20 forced + 12 mutex.

| Rank | Pair | lift | conf | read |
|---:|---|---:|---:|---|
| 1–2 | `surv_no_coverage` ↔ `center_offline` | 3.52 | 100% | **genuine** — total surveillance loss always co-occurs with the en-route center being offline |
| 3–6 | `comm_total_failure` ↔ `twr_ground_control` / `twr_closed` | 2.30–2.37 | ~50% | comm-failure hub; tower degraded states |
| 7–8 | `surv_full_coverage` ↔ `center_adsb_only` | 1.80 | — | surveillance/center coupling |
| 9–14 | `comm_total_failure` ↔ `tracon_*` / `center_offline` | 1.52–1.57 | — | same comm-failure hub projecting outward |

`comm_total_failure` is the dominant hub here (support 4.4%, rides nearly every top pair). The one clean standout is the `surv_no_coverage`→`center_offline` (conf 100%) dependency.

## Symbolic scanner — 52 candidates (state-rich model)
Highest-impact, present-root candidates (trace cut):

| Suggested REJECT (informal) | Cut | % |
|---|---:|---:|
| `surv_full_coverage` requires `surv_adsb_only` ∨ `surv_degraded_ssr_only` | 5,003 | 27.8% |
| `center_flow_restricted` requires `surv_adsb_only` | 3,914 | 21.7% |
| `comm_voice_only` / `comm_cpdlc_only` requires `surv_adsb_only` | 3,110 | 17.3% |
| `ac_emergency` requires `ac_diverting` (Shape C) | 1,466 | 8.1% |

Many other Shape-B rows fire only because of the missing weather/flow ROOTs (e.g. "requires `wx_low_visibility_ops`" / "requires `flow_gdp_active`") and should be ignored until the trace space is regenerated.

## Structural
- **Unreachable state (present roots):** `center_sector_active` — never appears in any trace.
- **Missing ROOTs:** `Flow_Management`, `Weather_System` (see top warning).

## Bottom line
ATC's most important finding is the **trace-file/schema mismatch**. Once regenerated, the `surv_no_coverage → center_offline` dependency and the comm-failure cluster are the candidates for the SME tool.
