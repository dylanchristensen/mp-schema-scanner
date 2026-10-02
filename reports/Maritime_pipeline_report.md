# Maritime Port Logistics — Pipeline Run

**Model:** `Maritime_Port_Logistics_Composed.mp` (8 ROOTs, 36 states, 4 orderings, 12 REJECTs)
**Trace space:** 45,836 traces (`..._Constrained_scope_1.gry`, 967 MB) — the largest space in the set.
**Run date:** 2026-06-21 · Pipeline: symbolic scan + Direction A lift (constrained-only). All 8 ROOTs present.

## Headline candidate
**`gnss_jammed` ↔ `ais_offline` / `ais_rx_only`** (lift 1.91, conf 50%). GNSS
jamming co-occurs with AIS degradation — a genuine cyber-physical emergent
(a jamming/spoofing event taking down position reporting). Not forced by any
single REJECT. Top candidate for the SME tool.

## Direction A — top implicit candidates (lift)
1,010 cross-ROOT pairs → 1,000 implicit after removing 10 forced (0 mutex).

| Rank | Pair | lift | conf | read |
|---:|---|---:|---:|---|
| 1–4 | `vessel_moored` ↔ `berth_available` / `berth_occupied` | 1.95 | 50% | berthing structure (mostly expected) |
| 5–8 | `gnss_jammed` ↔ `ais_rx_only` / `ais_offline` | 1.91 | 50% | **genuine** — jamming → AIS loss (see headline) |
| 9–12 | `colregs_give_way` ↔ `vts_monitoring` / `vts_offline` | 1.59 | — | collision-avoidance vs vessel-traffic-service coupling |
| 13–15 | `vessel_altering_course` ↔ `ecdis_nominal` / `nav_degraded` | 1.26 | — | maneuvering vs nav-system state |

## Symbolic scanner — 7 candidates

| Suggested REJECT (informal) | Cut | % | note |
|---|---:|---:|---|
| `tugs_assisting` requires `tugs_dispatched` (Shape A) | 12,404 | 27.1% | vacuous-foreach: tugs assisting without ever being dispatched |
| `ais_tx_rx_active` requires `vessel_moored` | 10,624 | 23.2% | likely over-fire |
| `colregs_stand_on` requires `vessel_altering_course` ∨ `vessel_stopping` | 9,440 | 20.6% | COLREGS pairing — worth a look |
| `ais_tx_rx_active` requires `berth_occupied` | 8,118 | 17.7% | over-fire |
| `vessel_altering_course` requires `colregs_give_way` | 8,160 | 17.8% | maneuver-without-rule candidate |
| `vessel_moored` requires `berth_allocated` | 1,260 | 2.7% | moored with no berth allocation — clean candidate |
| `colregs_give_way` requires `vts_issuing_warning` | 1,280 | 2.8% | give-way without VTS warning |

## Structural
- **Unreachable state:** `cargo_ops_active` — never appears in any trace.

## Bottom line
Strongest of the new models: a real cyber-physical emergent (**GNSS jamming →
AIS loss**) plus clean scanner candidates (tugs-without-dispatch,
moored-without-berth). Feed those to the SME tool.
