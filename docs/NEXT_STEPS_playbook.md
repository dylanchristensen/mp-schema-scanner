# Next Step: the SME-in-the-loop iteration (worked on Smart Home, template for all models)

The pipeline produces a *candidate set*. The next step is the loop that turns
candidates into either schema fixes or recorded emergent behaviors. Smart home
is the worked example here; the same six steps apply to SCADA, ATC, Maritime,
and Smart Street.

## The loop

1. **Triage structural issues first.** Unreachable states and missing ROOTs are
   bugs that corrupt every statistic downstream — fix them before any
   adjudication.
2. **Run the pipeline** → symbolic scan + Direction A candidate set.
3. **Adjudicate** each candidate (your SME trace tool) into one of three:
   *modeling gap*, *genuine emergent*, or *false positive*.
4. **For a modeling gap:** add the REJECT, **re-enumerate, and re-run.**
   Key shortcut — a presence-REJECT is *monotonic* (it only removes traces), so
   re-enumeration for a REJECT-only edit is just **filtering the current trace
   set**; you do *not* need to re-run MP. Repeat until no new gaps surface.
5. **For a genuine emergent:** record it as an implicit edge in the Assumption
   Graph and extract the gadget chain (the weird-machine, à la healthcare
   Trace 19). These are *not* fixed with a REJECT — the system really permits
   them.
6. **Know when to stop.** When the residual top of the ranking is *hub-dominated*
   (one or two states riding nearly every top pair), you've found the gaps;
   what's left is schema-induced noise that needs the schema-aware filter, not
   more REJECTs.

## Worked example — Smart Home, one full iteration

**Candidate set (from the pipeline):** 8 symbolic + Direction-A top-25.
Adjudication verdicts:

| Candidate | Verdict | Action |
|---|---|---|
| **B1** `vehicle_charging` needs a source | **modeling gap** | add REJECT (twin of the existing `battery_charging` rule) |
| **C2** `demand_response_event` needs `gateway_online` | **modeling gap** | add REJECT (DR signal arrives over comms) |
| A1 `battery_discharging` needs `grid_services_mode` | false positive | none (home self-consumption is legitimate) |
| C1 `battery_discharging` needs `exporting_power` | false positive | none (discharge can power the home) |
| B2/B4/B5 HEMS modes need comms | false positive | none (local autonomous policies) |
| B3 `manual_override_mode` needs comms | false positive | none (override is deliberately local) |

**Apply the two gaps → re-enumerate (filter) → re-run:**

| | baseline | after iteration 1 |
|---|---:|---:|
| traces | 18,080 | **15,512** (−14.2%; 924 B1 + 1,800 C2, union 2,568) |
| explicit (forced) pairs | 22 | **28** — B1/C2 pairs now *explained*, dropped from the implicit ranking |
| top candidate | `grid_outage ↔ loads_shed_for_dr` (lift 2.34) | `grid_outage ↔ loads_shed_for_dr` (lift 2.11) |

The gaps are closed (the EV-source and DR-comms pairs no longer appear as
implicit candidates), but the **top is still the `grid_outage` / `loads_shed` /
`gateway` hub cluster** — schema-induced by the outage operating-envelope
REJECTs, not new gaps. That's the step-6 stop signal: two REJECTs exhausted the
genuine gaps; the rest is the schema-aware-filtering problem.

Artifacts: `Smart_Home_Energy_Composed_patched.mp` (schema with the two SME
REJECTs appended) is in this folder.

## What to do for each of the other models

| Model | Do first (structural) | Then adjudicate (top candidates) |
|---|---|---|
| **SCADA** | fix `breaker_open` unreachable (transition-as-state) | `line_faulted + breaker_closed` (likely **emergent** → gadget: fault-not-cleared); A1 false-GOOSE-trip; A2 spurious-breaker |
| **ATC** | **regenerate the trace file from the full 8-ROOT model** (Flow_Management + Weather_System are missing); fix `center_sector_active` unreachable | `surv_no_coverage → center_offline` (conf 100%); the comm-failure cluster |
| **Maritime** | fix `cargo_ops_active` unreachable | `gnss_jammed → ais_offline` (**emergent** → gadget: jamming → position-reporting loss); `tugs_assisting` without dispatch (gap); `vessel_moored` without berth (gap) |
| **Smart Street** | fix `av_braking_emergency` unreachable (safety-critical) | `av_cruising + object_detected` / `vru_in_roadway` (**emergent?** → safety gadget); braking/`ev_responding` Shape-B are false positives |

The pattern across all five: a small number of genuine gaps per model, one or
two genuine emergents worth a gadget chain, and a residual hub that motivates
the schema-aware filter as the real remaining research task.
