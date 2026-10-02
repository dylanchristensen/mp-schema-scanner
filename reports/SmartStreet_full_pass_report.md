# Smart Street V2X — Full Verification Pass — 2026-07-21

Model: `Connected_Street_V2X_Composed.mp` (8 ROOTs, 32 states, 12 REJECTs,
6 orderings, 5 COORDINATEs). Everything below verified against the MP-generated
trace data and the validated closed-form enumerator.

## 1. Trace space: verified exactly, three ways

| Source | Traces |
|---|---:|
| MP Gryphon export (`.gry`) | 24,536 |
| SQLite DB (`gry_parse.py`) | 24,536 |
| Closed-form enumeration (`mp_enumerate.py`), from 61,440 possible | 24,536 |

Beyond the count: per-state supports match exactly, and the **full trace
multisets are identical** between the MP run and the enumerator. The Smart
Street space is fully reproducible from the schema text alone.

## 2. Schema audit

**Orderings.** Four of six hold vacuously-in-the-good-sense (both events in
one state, grammar-ordered): obstacle→trajectory, preempt→terminate,
terminate→dwell, hazard→DENM. **Two are cross-ROOT and delete traces:**

- `ttc_below_threshold BEFORE aeb_activated` — deletes every
  `collision_predicted` × `av_braking_emergency` trace (3,072)
- `tx_high_priority_bsm BEFORE hazard_detected` — deletes every
  `ev_responding` × `mec_hazard_broadcasting` trace (5,120)

**Dead rules (verified: can never fire, 0 possible violations):**

| Rule | Why dead |
|---|---|
| `tc_coord_normal AND tc_preempt_active` | same-ROOT siblings; mutually exclusive by alternation |
| `obu_cooperative_perception AND obu_isolated` | same |
| `rx_spat AND obu_isolated` | rx_spat only occurs in obu_isolated's siblings |
| `trajectory_adjusted AND NOT object_detected AND NOT collision_predicted` | trajectory_adjusted only occurs inside object_detected |

Harmless but misleading — they document intent the alternation already
enforces, and they inflate the apparent rule coverage.

## 3. Structural findings

### Finding 1 (known): emergency braking is impossible
`av_braking_emergency` has zero support. REJECT 1 requires AEB to co-occur
with `collision_predicted`; the cross-ROOT ordering deletes every trace where
they do. Waterfall: the ordering removes 3,072 traces, REJECT 1 removes the
remaining 9,216 — together all 12,288 AEB traces (20% of the space).
Note: COORDINATE 5 (`evasive_trajectory_planned PRECEDES aeb_activated`) was
plausibly *intended* to order these roots, but the MP run confirms the ENSURE
still deletes the pair — coordination did not rescue the workflow.

### Finding 2 (NEW): the EV-to-hazard-broadcast pathway is impossible
`ev_responding` × `mec_hazard_broadcasting` = **0 of 24,536** traces
(9,252 and 1,724 respectively — never together). The ordering written to
sequence this exact V2X workflow ("EV must broadcast high priority BSM before
MEC detects hazard") deletes it instead. Consequences:
- The `ev_responding` disjunct of the hazard-source REJECT is dead code;
  hazard broadcasting only ever fires via `vru_in_roadway` or
  `collision_predicted`.
- The model cannot represent the canonical emergency scenario the
  standard (ETSI DENM) exists for: an ambulance triggering a hazard broadcast.

Same mechanism as smart-home DR shedding and the AEB kill: cross-ROOT
ENSURE over uncoordinated roots.

## 4. Rule waterfall (orderings first, then REJECTs in file order)

Removals sum exactly: 61,440 − 24,536 = 36,904.

| Rule | Cut |
|---|---:|
| ORD ttc BEFORE aeb | 3,072 |
| ORD bsm BEFORE hazard | 4,864 |
| REJ AEB requires collision | 8,448 |
| REJ cruising × collision | 2,816 |
| REJ cruising × sensor_degraded | 2,816 |
| REJ green × flash_fault | 2,464 |
| REJ preempt requires EV | 7,168 |
| REJ hazard needs source | 2,904 |
| REJ cruising × red × spat | 756 |
| REJ accelerating × VRU connected | 1,596 |
| (4 dead rules) | 0 |

## 5. Symbolic scanner (Shapes A–C) + worklist

7 candidates, all Shape B, quantified on the space and reduced to **15 review
patterns**. Proposed verdicts (SME to confirm): **all seven false positives** —
six propose "X requires ev_responding" for states with no EV dependency
(intentional asymmetry of the preemption rule), and B4 proposes normal braking
requires a collision prediction (routine braking needs none). High cut rates
(15–23%) support this: genuine gaps historically cut ≤10%.

The scanner catches **none** of the real defects in Sections 2–3 — direct
motivation for the planned Shape D (sibling-mutex REJECT), Shape E (cross-ROOT
ordering deletion), and Shape F (within-state order contradiction) detectors.

## 6. Co-occurrence flag (paper configuration)

m=420 family, **160 trends** (82 clinging / 78 excluding), 93 Bonferroni /
137 BH survivors. Hub analysis confirms the smart-home lesson: the top hub
states are exactly the rule-wired ones — `mec_hazard_broadcasting` (19 trends),
`vru_in_roadway` (19), `collision_predicted` (17), `ev_responding` (17).
Schema-induced structure dominates; 16 trends are pairs named together by a
single REJECT.

## 7. Recommended schema fixes (then regenerate & re-run)

1. Remove or rewrite the 4 dead rules (replace the intent as comments, or as
   correct cross-ROOT forms where one exists).
2. Fix the two killing orderings: either model the coordination the BEFORE
   assumes (so the events are genuinely ordered), or express the intent as
   presence rules instead of orderings.
3. After the fix, AEB and EV-hazard workflows become reachable; re-run the
   full pipeline to re-derive flags on the corrected space (the
   detect→fix→re-enumerate loop on a non-toy model).
