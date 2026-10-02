## INSuRE+C Schema Scanner

Schema:  D:\Research\NSA INSuRE+C\Summer\Models + Writeups\SCADA\Power_Grid_SCADA_Composed.mp
Traces:  (none provided)
States:  31  Orderings: 4  REJECTs: 9

Total candidate findings: 9
  Shape A: 2
  Shape B: 7
  Shape C: 0

### Shape A -- vacuous-foreach gaps

A1. Ordering 'protection_pickup BEFORE publishing_goose_message' is vacuously satisfiable when ied_issuing_goose_trip is active but ied_overcurrent_detected is absent. No REJECT enforces ied_issuing_goose_trip -> (ied_overcurrent_detected).
    Suggested REJECT:
        IF #ied_issuing_goose_trip > 0 AND #ied_overcurrent_detected == 0 THEN REJECT; FI;

A2. Ordering 'high_fault_current BEFORE trip_coil_energized' is vacuously satisfiable when breaker_opening is active but line_faulted is absent. No REJECT enforces breaker_opening -> (line_faulted).
    Suggested REJECT:
        IF #breaker_opening > 0 AND #line_faulted == 0 THEN REJECT; FI;

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'ems_load_shedding requires (ami_disconnect_active)'. dist_peak_load (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #dist_peak_load > 0 AND #ami_disconnect_active == 0 THEN REJECT; FI;

B2. Schema has rule 'dist_feeder_fault requires (ami_blackout_detected)'. dist_nominal (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #dist_nominal > 0 AND #ami_blackout_detected == 0 THEN REJECT; FI;

B3. Schema has rule 'dist_feeder_fault requires (ami_blackout_detected)'. dist_peak_load (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #dist_peak_load > 0 AND #ami_blackout_detected == 0 THEN REJECT; FI;

B4. Schema has rule 'ems_load_shedding requires (ami_disconnect_active)'. ems_agc_active (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ems_agc_active > 0 AND #ami_disconnect_active == 0 THEN REJECT; FI;

B5. Schema has rule 'ems_load_shedding requires (ami_disconnect_active)'. ems_nominal (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ems_nominal > 0 AND #ami_disconnect_active == 0 THEN REJECT; FI;

B6. Schema has rule 'ot_net_partitioned requires (scada_blind)'. ot_net_congested (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ot_net_congested > 0 AND #scada_blind == 0 THEN REJECT; FI;

B7. Schema has rule 'ot_net_partitioned requires (scada_blind)'. ot_net_nominal (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ot_net_nominal > 0 AND #scada_blind == 0 THEN REJECT; FI;

### Shape C -- optional-event escalation

(no candidates)
