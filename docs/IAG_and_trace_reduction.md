# The Assumption Graph + how it makes the traces reviewable

Two things were missing from the runs so far: the **Implicit Assumption Graph
(IAG)** itself, and the step that turns a too-large trace space into something a
human can actually look at. They are the same thing — the IAG *is* the reduction
mechanism. Worked here on smart home (18,080 traces).

## 1. The Assumption Graph (drawn)

See `smart_home_IAG.png`. Nodes are component states, grouped by ROOT. Edges are
the dependency assumptions:

- **black "requires"** — explicit edges parsed from `REJECT IF #X>0 AND #Y==0`
  (a `∨` diamond means "requires at least one of").
- **red "mutex"** — `REJECT IF #X>0 AND #Y>0` (states that exclude each other).
- **grey "if outage"** — the conditional outage-envelope rules.
- **blue "before"** — ordering (`ENSURE FOREACH … BEFORE …`).
- **orange bold** — the one *implicit* edge we **discovered** by adjudication
  (`vehicle_charging` requires a source). This is the kind of edge the whole
  method exists to find: the designer assumed it but never wrote it down.

From the schema: 7 explicit requires-edges, 2 mutex, 5 conditional, 3 orderings.
The SME grows the graph by adding discovered implicit edges (currently 1).
**The graph, not the trace list, is the unit of review.**

## 2. Why the traces stop being "too numerous"

The trace space is 18,080. The 8 detection signals flag **10,048** traces — 56%
of the space, useless to eyeball directly. The fix: a flagged trace only matters
through the *edge* it violates, so project each flagged set onto just the
components that edge touches and dedupe. The 10,048 traces collapse to **23
distinct review patterns**:

| signal | antecedent (present) | flagged traces | distinct patterns | components |
|---|---|---:|---:|---|
| A | `battery_discharging` (no grid-services) | 4,720 | 4 | hems, home_battery |
| C | `battery_discharging` (no export) | 3,000 | 3 | grid_connection, home_battery |
| B | `manual_override_mode` (no comms) | 2,236 | 2 | comm_gateway, hems |
| C | `demand_response_event` (no comms) | 1,800 | 2 | comm_gateway, grid_connection |
| B | `backup_reserve_mode` (no comms) | 1,488 | 2 | comm_gateway, hems |
| B | `self_consumption_mode` (no comms) | 1,488 | 2 | comm_gateway, hems |
| B | `time_of_use_mode` (no comms) | 1,488 | 2 | comm_gateway, hems |
| B | `vehicle_charging` (no source) | 924 | 6 | ev_system, grid_connection, solar_inverter |

**18,080 traces → 23 patterns** to review (one witness trace each). After the SME
dismisses the false-positive edges (the `battery_discharging` and HEMS-mode
over-fires), only the genuine edges remain — `vehicle_charging`-no-source and
`demand_response_event`-no-comms — i.e. **~8 patterns**. That is the
"narrow 10,000 to 200" claim made concrete (here, 18,080 → ~8).

### Why co-occurrence alone gave nothing
At the Spring ≥80%-confidence rule, smart home has only 2 strong cross-component
dependencies and **both are perfect (zero exceptions)** — so co-occurrence
breaking flags no traces. The reviewable set here comes entirely from the
structural signals (vacuous-foreach + symmetric/escalation), reduced by
projection. (Consistent with the yield-tracks-schema-completeness thesis.)

## How to apply to the other models
1. Build the IAG from the schema (`iag_dot.py <model.mp> out.dot; dot -Tpng`).
2. Run the signals, then collapse flagged traces to patterns
   (`reduce2.py <model.mp> <db>`).
3. Hand the SME tool the *distinct patterns* (with witnesses), not the raw
   traces. Each adjudicated pattern either adds an implicit edge to the IAG or
   gets dismissed.

Artifacts in this folder: `smart_home_IAG.png`, `smart_home_iag.dot`,
`iag_dot.py`, `reduce2.py`.
