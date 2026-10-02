## INSuRE+C Schema Scanner

Schema:  D:\Research\NSA INSuRE+C\Summer\Models + Writeups\Smart Home\Smart_Home_Energy_Composed.mp
Traces:  (none provided)
States:  30  Orderings: 3  REJECTs: 14

Total candidate findings: 8
  Shape A: 1
  Shape B: 5
  Shape C: 2

### Shape A -- vacuous-foreach gaps

A1. Ordering 'commanding_export BEFORE delivering_energy' is vacuously satisfiable when battery_discharging is active but grid_services_mode is absent. No REJECT enforces battery_discharging -> (grid_services_mode).
    Suggested REJECT:
        IF #battery_discharging > 0 AND #grid_services_mode == 0 THEN REJECT; FI;

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'battery_charging requires (importing_power | solar_curtailed | solar_producing)'. vehicle_charging (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #vehicle_charging > 0 AND #importing_power == 0 AND #solar_curtailed == 0 AND #solar_producing == 0 THEN REJECT; FI;

B2. Schema has rule 'grid_services_mode requires (gateway_online)'. backup_reserve_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #backup_reserve_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;

B3. Schema has rule 'grid_services_mode requires (gateway_online)'. manual_override_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #manual_override_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;

B4. Schema has rule 'grid_services_mode requires (gateway_online)'. self_consumption_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #self_consumption_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;

B5. Schema has rule 'grid_services_mode requires (gateway_online)'. time_of_use_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #time_of_use_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;

### Shape C -- optional-event escalation

C1. REJECT triggered by optional event 'sending_to_grid' of state 'battery_discharging'. When 'sending_to_grid' does not fire, 'battery_discharging' can be active without requiring (exporting_power). Escalating to parent state closes this gap.
    Suggested REJECT:
        IF #battery_discharging > 0 AND #exporting_power == 0 THEN REJECT; FI;

C2. REJECT triggered by optional event 'curtailment_applied' of state 'demand_response_event'. When 'curtailment_applied' does not fire, 'demand_response_event' can be active without requiring (gateway_online). Escalating to parent state closes this gap.
    Suggested REJECT:
        IF #demand_response_event > 0 AND #gateway_online == 0 THEN REJECT; FI;
