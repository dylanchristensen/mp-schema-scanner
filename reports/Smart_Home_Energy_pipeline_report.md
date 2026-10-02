# Smart Home Energy — Full Pipeline Run

**Model:** `Smart_Home_Energy_Composed.mp` (7 ROOTs, 30 states, 3 orderings, 14 REJECTs)
**Constrained trace space:** 18,080 traces (`constrained.gry`, 245 MB)
**Unconstrained baseline:** 57,600 traces (`unconstrained.gry`, 835 MB)
**Run date:** 2026-06-21 · NSA INSuRE+C Summer 2026

This report runs all three detection layers end-to-end on the smart-home model
and adjudicates the candidates. It is the smart-home analog of the Spring
healthcare end-to-end result, at ~500× the trace count.

> **SME verdicts below are *proposed* (my reasoning), not confirmed ground
> truth.** They turn on domain judgment about residential energy systems and
> should be reviewed before any schema edit.

---

## Headline

All three layers converge on the same scaling lesson the abstract predicts:
on a **constraint-rich** model, the statistical signals (lift, z-test) are
**dominated by schema-induced structure** — here two hubs, `gateway_online`
and `grid_outage` — and genuinely novel findings are rare. The **symbolic
gap scanner is the most precise layer**: 8 concrete candidates, of which
about **two look like real modeling gaps** (EV charging without a source;
DR event without communications) and the rest are **semantically-justified
asymmetries** an SME would reject.

---

## Layer 1 — Symbolic gap scanner (schema-only)

8 candidate `REJECT` rules from Shapes A/B/C. Each is quantified here against
the 18,080-trace space (how many traces the proposed rule would eliminate).

| ID | Proposed REJECT (informal) | Traces cut | % | Proposed verdict |
|----|----------------------------|-----------:|----:|------------------|
| **B1** | `vehicle_charging` requires a source (import/solar/battery) | 924 | 5.1% | **GENUINE GAP** — EV is a load; physically needs a source. Schema has the symmetric rule for `battery_charging` but omits it for the EV. Highest-value finding. |
| **C2** | `demand_response_event` requires `gateway_online` | 1,800 | 10.0% | **GENUINE GAP** — a DR event begins with `dr_signal_received`, which arrives over comms. Can't have a DR event with the gateway down. |
| A1 | `battery_discharging` requires `grid_services_mode` | 4,720 | 26.1% | FALSE POSITIVE — home battery routinely discharges for self-consumption with no grid-services enrollment. |
| C1 | `battery_discharging` requires `exporting_power` | 3,000 | 16.6% | FALSE POSITIVE — discharge can power the home; export is optional (`[sending_to_grid]`). |
| B3 | `manual_override_mode` requires `gateway_online` | 2,236 | 12.4% | FALSE POSITIVE — override is explicitly local owner control; offline is the point. |
| B2 | `backup_reserve_mode` requires `gateway_online` | 1,488 | 8.2% | LIKELY FALSE POSITIVE — autonomous local HEMS policy; no utility comms needed. |
| B4 | `self_consumption_mode` requires `gateway_online` | 1,488 | 8.2% | LIKELY FALSE POSITIVE — local policy. |
| B5 | `time_of_use_mode` requires `gateway_online` | 1,488 | 8.2% | LIKELY FALSE POSITIVE — local schedule; only `grid_services_mode` genuinely needs comms (talks to the VPP/utility). |

**Read of the B-group:** the symmetric-completion shape fires on all four HEMS
siblings of `grid_services_mode`, but the asymmetry in the schema is
*intentional* — only grid services talks to the utility. This is a clean
illustration of the shape over-generating and the SME doing the real work.

---

## Layer 2 — Direction A (single-set lift)

748 cross-ROOT ordered pairs → 728 implicit candidates after removing 20
REJECT-forced pairs, ranked by lift.

**Top of the ranking is schema-induced.** The lift top-25 is dominated by
`grid_outage` co-occurrences — `loads shed for dr ↔ grid outage` (lift 2.34),
`solar sleeping ↔ grid outage` (1.53), `loads idle ↔ grid outage` (1.40),
etc. These cling together because the outage operating-envelope REJECTs *force*
them to, not because of any hidden assumption.

**The genuinely interesting assumptions sink.** Where the pre-registered
"real" assumptions actually land:

| Implicit assumption (pre-registered) | Lift rank | lift |
|---|---:|---:|
| DR event needs comms (`demand_response_event → gateway online`) | 67 / 728 | 1.17 |
| EV charging needs a source (`vehicle charging → importing power`) | 163 / 728 | 1.03 |
| EV charging needs a source (`→ solar producing`) | 166 / 728 | 1.03 |
| Self-consumption needs solar | 505 / 728 | 0.99 |
| HEMS mode needs comms | 633–638 / 728 | 0.89 |

On this constraint-rich model, **lift does not surface the real assumptions to
the top** — they're buried below schema-induced noise. This is exactly the
"yield tracks schema completeness" finding, reproduced at scale.

---

## Layer 3 — Direction B (differential z-test)

Unconstrained (57,600) vs constrained (18,080), two-proportion pooled z,
Bonferroni-corrected. **313 significant findings:** 24 single-state
(10 suppressed / 14 boosted), 285 co-occurrence (128 / 157), 4 precedence.

- **Suppressed** = what the REJECTs killed, as intended: `loads shed for dr`
  (25.0%→5.0%, z=−58.6), `grid services mode` (−44.9), `grid outage` (−36.0).
  Sanity check that the constraints fire.
- **Boosted** = side effects. Every top boosted co-occurrence involves
  `gateway_online` (`+ loads idle`, `+ manual override`, `+ importing power`,
  `+ battery depleted` …). Because so many REJECTs *require* `gateway_online`,
  constraining the space inflates its prevalence and everything riding along
  with it — again schema-induced, not emergent.
- Only boosted precedence: `coordinating_devices BEFORE cloud_connected`.

**Same conclusion from the other direction:** the differential signal is
hub-dominated. 285 "significant" co-occurrences is not 285 findings — it's two
hubs (`gateway_online`, `grid_outage`) projecting across the model.

---

## What this says about scaling the pipeline

1. **Symbolic > statistical on constraint-rich models.** The schema-only
   scanner produced 8 reviewable candidates with a ~2/8 genuine-gap yield.
   The statistical layers produced 728 (lift) and 313 (z-test) ranked items
   whose tops are schema artifacts. For an SME's time, the scanner wins here.
2. **The hub problem is the real obstacle to scale.** `gateway_online` and
   `grid_outage` dominate both statistical rankings. This is concretely the
   "automated schema-aware filtering" challenge the abstract names — suppress
   pairs that a single REJECT already explains and the genuine candidates
   should rise.
3. **Yield is modest and that's the point.** ~2 genuine gaps from a
   well-specified 14-REJECT schema is consistent with the thesis: the more
   completely the schema already encodes intent, the fewer genuine emergents
   remain.

## Suggested next actions

- **Confirm the two genuine-gap verdicts** (B1 EV-source, C2 DR-needs-comms).
- If confirmed, **add the two REJECTs, regenerate, and re-run** — closes the
  detect→fix→re-enumerate loop on a non-toy model.
- **Prototype the schema-aware filter** (the "pairwise mandate check" from the
  decision memo): drop any statistical pair both halves of which a single
  REJECT already mentions, and re-rank. Smart home is the right test case
  because the hub effect is so visible.

---

## Appendix — reproduction

- **Direction A:** `python explore_lift_smart_home.py` (uses
  `smart_home_constrained_traces.db`, table `trace_states_constrained`).
- **Symbolic scan:** `python scanner.py Smart_Home_Energy_Composed.mp`
- **Candidate quantification:** counts run as SQL over the constrained DB
  (state labels are stored space-separated, e.g. `battery discharging`).
- **Direction B:** existing `differential_analysis_results.txt`
  (re-running needs the 835 MB unconstrained set; not re-parsed here due to
  the 3.8 GB sandbox memory ceiling).
