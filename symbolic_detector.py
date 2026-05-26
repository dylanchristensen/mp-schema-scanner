"""
Symbolic detector for schema silences -- the half lift cannot see.

Three detectors:

  Shape A -- Vacuous-foreach gap.
    For each ENSURE FOREACH (event_A BEFORE event_B), the ordering is
    vacuously satisfiable in any trace where consequent_state(event_B)
    is active but event_A never fires. The expected counterpart is a
    REJECT enforcing that consequent_state(event_B) requires
    consequent_state(event_A) (or an alternative source of event_A).
    Flag if no such REJECT exists.

  Shape B -- Symmetric REJECT completion.
    For each existing REJECT "X requires {Y_i}", find analogous states
    (same-ROOT siblings sharing a descriptor token or role tag, or
    cross-ROOT lexical analogs sharing a non-passive name token) that
    (a) are not passive and (b) have no REJECT requiring any of {Y_i}.
    Flag those as candidates for an analogous rule.

  Shape C -- Optional-event escalation.
    For each REJECT triggered by an OPTIONAL event of state X, the rule
    only fires when the optional event happens to fire. If the schema
    intent is "X always requires Y", the rule should be escalated to
    the parent state X. Flag candidates where this escalation has no
    existing parent-state-level counterpart.

Output: a ranked candidate list per detector with rationale and a
suggested REJECT clause.
"""
from __future__ import annotations
from schema_parser import parse_schema, Schema, Reject


# Helpers --------------------------------------------------------------

# Event-verb role tags. Used to detect when an existing REJECT's
# antecedent (e.g., battery_charging-an-energy-sink) is being matched
# against an analogous candidate playing the opposite role
# (e.g., battery_discharging-an-energy-source).
ROLE_VERB_TAGS = {
    "producing":   "source",
    "delivering":  "source",
    "sending":     "source",
    "providing":   "source",
    "supplying":   "source",
    "dispensing":  "source",
    "absorbing":   "sink",
    "drawing":     "sink",
    "consuming":   "sink",
    "receiving":   "sink",
    # We deliberately do NOT tag verbs like 'reading', 'reviewing',
    # 'assessing' -- those don't have a producer/sink role in the
    # energy/material-flow sense, and including them would over-filter.
}


PASSIVE_TOKENS = {
    "off", "closed", "down", "depleted", "idle", "unavailable",
    "none", "no", "not", "sleeping", "faulted", "offline",
    "powered_off", "out_of_service", "suspended", "standby",
    "off_duty", "powered", "recalibrating", "calibrating", "updating",
    "outage", "pending",
}


def is_passive_state(state: str) -> bool:
    """True if the state name's meaning is an inactive/disengaged form."""
    s = state.lower()
    tokens = s.split("_")
    for tok in tokens:
        if tok in PASSIVE_TOKENS:
            return True
    return False


def ident_to_state(schema: Schema, ident: str) -> str | None:
    """Resolve an identifier (state or event) to its owning state."""
    if ident in schema.state_root:
        return ident
    if ident in schema.event_to_state:
        return schema.event_to_state[ident]
    return None


def reject_positives_as_states(schema: Schema, r: Reject,
                                mandatory_only: bool = False,
                                schema_for_optional=None) -> set[str]:
    """Resolve REJECT positive identifiers to owning states.

    If mandatory_only is True, skip identifiers that are optional events
    (in square brackets) of their owning state -- those only credit
    coverage when the optional event happens to fire.
    """
    out = set()
    for p in r.positives:
        st = ident_to_state(schema, p)
        if not st:
            continue
        if mandatory_only and p in schema.event_to_state and p != st:
            evs = schema.consequents.get(st, [])
            for ev_name, is_opt in evs:
                if ev_name == p and is_opt:
                    break
            else:
                out.add(st)
                continue
            continue
        out.add(st)
    return out


def reject_negatives_as_states(schema: Schema, r: Reject) -> set[str]:
    return {s for s in (ident_to_state(schema, n) for n in r.negatives) if s}


def has_consequent_events(schema: Schema, state: str) -> bool:
    return bool(schema.consequents.get(state))


def reject_covers(schema: Schema, x: str, y: str,
                  mandatory_only: bool = True) -> bool:
    """True if ANY REJECT enforces 'x present implies y present'."""
    for r in schema.rejects:
        pos = reject_positives_as_states(
            schema, r, mandatory_only=mandatory_only)
        neg = reject_negatives_as_states(schema, r)
        if x in pos and y in neg:
            return True
    return False


def descriptor_tokens(schema: Schema, state: str) -> set[str]:
    """Tokens of the state name with the ROOT-name prefix stripped."""
    root = schema.state_root.get(state, "")
    root_toks = {t.lower() for t in root.split("_")}
    out = set()
    for tok in state.split("_"):
        if tok in PASSIVE_TOKENS:
            continue
        if tok.lower() in root_toks:
            continue
        out.add(tok)
    return out


def share_nontrivial_token(schema: Schema, a: str, b: str) -> bool:
    """True if a and b share a non-passive, non-component-noun descriptor."""
    ta = descriptor_tokens(schema, a)
    tb = descriptor_tokens(schema, b)
    shared = {t for t in (ta & tb) if len(t) >= 2 and t.isalpha()}
    return bool(shared)


def state_role(schema: Schema, state: str) -> str | None:
    """Return 'source', 'sink', or None based on event verbs."""
    seen = set()
    for ev_name, _opt in schema.consequents.get(state, []):
        for tok in ev_name.split("_"):
            tag = ROLE_VERB_TAGS.get(tok)
            if tag:
                seen.add(tag)
    if seen == {"source"}:
        return "source"
    if seen == {"sink"}:
        return "sink"
    return None


def is_mutex(schema: Schema, x: str, y: str) -> bool:
    """True if the schema has a REJECT making x and y mutually exclusive."""
    for r in schema.rejects:
        if not r.is_mutex():
            continue
        ps = reject_positives_as_states(schema, r)
        if x in ps and y in ps:
            return True
    return False


# Detector A -----------------------------------------------------------

def detect_shape_a(schema: Schema) -> list[dict]:
    """Find ENSURE FOREACH orderings with no REJECT counterpart."""
    out = []
    for event_a, event_b in schema.orderings:
        x_a = schema.event_to_state.get(event_a)
        x_b = schema.event_to_state.get(event_b)
        if not x_a or not x_b:
            continue
        if x_a == x_b:
            continue

        if reject_covers(schema, x_b, x_a, mandatory_only=True):
            continue

        alt_sources = set()
        for ev_a2, ev_b2 in schema.orderings:
            if ev_b2 == event_b and ev_a2 != event_a:
                alt = schema.event_to_state.get(ev_a2)
                if alt and alt != x_a and schema.state_root[alt] == schema.state_root[x_a]:
                    alt_sources.add(alt)

        covered_by_disj = False
        if alt_sources:
            for r in schema.rejects:
                pos = reject_positives_as_states(schema, r)
                neg = reject_negatives_as_states(schema, r)
                if x_b in pos and (({x_a} | alt_sources) & neg):
                    covered_by_disj = True
                    break
        if covered_by_disj:
            continue

        if is_passive_state(x_b):
            continue

        out.append({
            "shape": "A",
            "ordering": (event_a, event_b),
            "x_a": x_a, "x_b": x_b,
            "alt_sources": sorted(alt_sources),
            "suggested_reject": (
                f"#{x_b} > 0 AND " +
                " AND ".join(
                    f"#{s} == 0" for s in sorted({x_a} | alt_sources)
                ) + " THEN REJECT"
            ),
            "rationale": (
                f"Ordering '{event_a} BEFORE {event_b}' is vacuously "
                f"satisfiable when {x_b} is active but {x_a} is absent. "
                f"No REJECT enforces {x_b} -> "
                f"({' | '.join(sorted({x_a} | alt_sources))})."
            ),
        })
    return out


# Detector B (formerly Shape C) ---------------------------------------

def detect_shape_b(schema: Schema) -> list[dict]:
    """Find analogous states that should have an analogous REJECT rule.

    Two analogy modes:
      (i)  same-ROOT sibling: another state in the antecedent's ROOT,
           filtered to require shared descriptor token OR shared
           source/sink role tag (mere co-membership in the ROOT is too
           weak).
      (ii) cross-ROOT lexical analog: any state across ROOTs sharing a
           non-passive name token with the antecedent (e.g.,
           battery_charging ~ vehicle_charging).
    """
    out = []
    for r in schema.rejects:
        if not r.is_single_pos_disjunction():
            continue
        ant_state = ident_to_state(schema, r.positives[0])
        if not ant_state:
            continue
        source_set = sorted(reject_negatives_as_states(schema, r))
        if not source_set:
            continue
        ant_root = schema.state_root[ant_state]
        ant_role_for_analogy = state_role(schema, ant_state)

        analogs = set()
        for sibling in schema.roots[ant_root]:
            if sibling == ant_state:
                continue
            shares_tok = share_nontrivial_token(schema, ant_state, sibling)
            sib_role = state_role(schema, sibling)
            shares_role = (ant_role_for_analogy is not None
                           and ant_role_for_analogy == sib_role)
            if shares_tok or shares_role:
                analogs.add((sibling, "same-root sibling"))
        for st in schema.state_root:
            if st == ant_state:
                continue
            if schema.state_root[st] == ant_root:
                continue
            if share_nontrivial_token(schema, ant_state, st):
                analogs.add((st, "shared-token analog"))

        ant_role = state_role(schema, ant_state)
        for cand, analogy in analogs:
            if is_passive_state(cand):
                continue
            if not has_consequent_events(schema, cand):
                continue
            cand_root = schema.state_root[cand]
            if any(schema.state_root.get(s) == cand_root for s in source_set):
                continue

            cand_role = state_role(schema, cand)
            if ant_role and cand_role and ant_role != cand_role:
                continue

            surviving_sources = [
                s for s in source_set if not is_mutex(schema, cand, s)
            ]
            if not surviving_sources:
                continue

            covered = False
            for r2 in schema.rejects:
                pos = reject_positives_as_states(
                    schema, r2, mandatory_only=True)
                neg = reject_negatives_as_states(schema, r2)
                if cand in pos and (set(surviving_sources) & neg):
                    covered = True
                    break
            if covered:
                continue

            source_set_final = sorted(surviving_sources)

            out.append({
                "shape": "B",
                "analog_of": (ant_state, source_set_final, r.raw.strip()),
                "candidate_state": cand,
                "candidate_root": cand_root,
                "analogy": analogy,
                "suggested_reject": (
                    f"#{cand} > 0 AND " +
                    " AND ".join(f"#{s} == 0" for s in source_set_final) +
                    " THEN REJECT"
                ),
                "rationale": (
                    f"Schema has rule '{ant_state} requires "
                    f"({' | '.join(source_set_final)})'. "
                    f"{cand} ({analogy}, active state) has no analogous rule."
                ),
            })
    seen = {}
    for c in out:
        key = (c["candidate_state"], tuple(c["analog_of"][1]))
        if key not in seen:
            seen[key] = c
        else:
            if c["analogy"] == "shared-token analog" and \
               seen[key]["analogy"] == "same-root sibling":
                seen[key] = c
    return list(seen.values())


# Detector C (formerly Shape D) ---------------------------------------

def detect_shape_c(schema: Schema) -> list[dict]:
    """Find REJECTs whose positive antecedent is an OPTIONAL event."""
    out = []
    for r in schema.rejects:
        if not r.is_single_pos_disjunction():
            continue
        ant = r.positives[0]
        if ant in schema.state_root:
            continue
        parent = schema.event_to_state.get(ant)
        if not parent:
            continue
        is_opt = False
        for ev_name, opt in schema.consequents.get(parent, []):
            if ev_name == ant:
                is_opt = opt
                break
        if not is_opt:
            continue

        source_set = sorted(reject_negatives_as_states(schema, r))
        if not source_set:
            continue

        covered = False
        for r2 in schema.rejects:
            pos = reject_positives_as_states(
                schema, r2, mandatory_only=True)
            neg = reject_negatives_as_states(schema, r2)
            if parent in pos and (set(source_set) & neg):
                covered = True
                break
        if covered:
            continue

        out.append({
            "shape": "C",
            "optional_event": ant,
            "parent_state": parent,
            "existing_reject": r.raw.strip(),
            "source_set": source_set,
            "suggested_reject": (
                f"#{parent} > 0 AND " +
                " AND ".join(f"#{s} == 0" for s in source_set) +
                " THEN REJECT"
            ),
            "rationale": (
                f"REJECT triggered by optional event '{ant}' of state "
                f"'{parent}'. When '{ant}' does not fire, '{parent}' "
                f"can be active without requiring "
                f"({' | '.join(source_set)}). Escalating to parent "
                f"state closes this gap."
            ),
        })
    return out


# Report ---------------------------------------------------------------

def report(schema_path: str, known_implicit: list[tuple] | None = None) -> None:
    schema = parse_schema(schema_path)
    print(f"\n{'=' * 80}")
    print(f"SYMBOLIC DETECTOR -- {schema_path}")
    print(f"{'=' * 80}")
    print(f"states: {len(schema.state_root)}  "
          f"orderings: {len(schema.orderings)}  "
          f"rejects: {len(schema.rejects)}")

    a_cands = detect_shape_a(schema)
    b_cands = detect_shape_b(schema)
    c_cands = detect_shape_c(schema)

    print(f"\nShape A candidates (vacuous-foreach gaps): {len(a_cands)}")
    print("-" * 80)
    for i, c in enumerate(a_cands, 1):
        print(f"  A{i}. {c['rationale']}")
        print(f"      suggested: {c['suggested_reject']}")

    # Sort Shape B: cross-ROOT analogies first (stronger evidence),
    # then same-root.
    b_cands.sort(key=lambda c: (c["analogy"] != "shared-token analog",
                                c["candidate_state"]))
    print(f"\nShape B candidates (symmetric REJECT completion): {len(b_cands)}")
    print("-" * 80)
    for i, c in enumerate(b_cands, 1):
        tag = "[cross-ROOT]" if c["analogy"] == "shared-token analog" else "[same-ROOT]"
        print(f"  B{i}. {tag} {c['rationale']}")
        print(f"      suggested: {c['suggested_reject']}")

    print(f"\nShape C candidates (optional-event escalation): {len(c_cands)}")
    print("-" * 80)
    for i, c in enumerate(c_cands, 1):
        print(f"  C{i}. {c['rationale']}")
        print(f"      existing: IF {c['existing_reject']} THEN REJECT")
        print(f"      suggested: {c['suggested_reject']}")

    if known_implicit:
        print(f"\nKnown implicit assumptions -- detector recall:")
        print("-" * 80)
        for label, target_state, required_set in known_implicit:
            target_set = set(required_set)
            found = None
            for c in a_cands:
                if c["x_b"] == target_state:
                    cand_set = {c["x_a"]} | set(c["alt_sources"])
                    if cand_set & target_set:
                        found = ("A", c)
                        break
            if not found:
                for c in b_cands:
                    if c["candidate_state"] == target_state:
                        if set(c["analog_of"][1]) & target_set:
                            found = ("B", c)
                            break
            if not found:
                for c in c_cands:
                    if c["parent_state"] == target_state:
                        if set(c["source_set"]) & target_set:
                            found = ("C", c)
                            break
            if found:
                shape, c = found
                print(f"  [RECOVERED via Shape {shape}] {label}")
                print(f"     -> {c['suggested_reject']}")
            else:
                print(f"  [MISSED] {label}  ({target_state} -> {sorted(target_set)})")


if __name__ == "__main__":
    # Healthcare known implicit assumptions (corrected schema).
    # Spring #3 (claim_approved requires clinical activity) is a
    # rule REFINEMENT (an existing OR-clause is too loose), not a
    # missing rule, so it is structurally outside the symbolic
    # detector's scope -- the lift detector catches that one.
    healthcare_known = [
        ("Spring #1: ehr_up_to_date requires measurement",
         "ehr_up_to_date",
         ["device_active"]),
        ("Spring #2: physician_reviewing requires data available",
         "physician_reviewing",
         ["ehr_up_to_date", "ehr_outdated"]),
        ("Spring #3: claim_approved requires clinical activity "
         "(rule refinement -- outside symbolic scope)",
         "claim_approved",
         ["physician_prescribing"]),
    ]
    report("healthcareDelivery_corrected.mp", healthcare_known)

    # Smart home pre-registered candidates.
    # Cand 2 and Cand 4 were over-eager pre-registrations:
    #   Cand 2 (loads_shed_for_dr -> gateway_online): the schema's
    #     OR-clause (DR_event OR manual_override) is correct as-is.
    #     The comm requirement attaches to demand_response_event,
    #     which IS caught (see Cand 3 / Shape C). Forbidding the
    #     manual-override path would break local owner control.
    #   Cand 4 (self_consumption_mode -> solar): confuses policy
    #     (HEMS configured for self-consumption -- persists 24/7)
    #     with runtime action (whether solar is actually producing).
    # Both omitted as they would represent incorrect candidates.
    smart_home_known = [
        ("Cand 1: vehicle_charging needs energy source",
         "vehicle_charging",
         ["solar_producing", "solar_curtailed",
          "importing_power", "battery_discharging"]),
        ("Cand 3: demand_response_event needs gateway online",
         "demand_response_event",
         ["gateway_online"]),
        ("Cand 5: HEMS active modes need gateway online",
         "self_consumption_mode",
         ["gateway_online"]),
        ("Cand 7: battery_discharging[sending] needs policy authorization",
         "battery_discharging",
         ["grid_services_mode", "manual_override_mode"]),
    ]
    report("Smart_Home_Energy_Composed.mp", smart_home_known)
