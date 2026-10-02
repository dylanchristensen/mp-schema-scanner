## INSuRE+C Schema Scanner

Schema:  D:\Research\NSA INSuRE+C\Summer\Models + Writeups\Maritime Port\Maritime_Port_Logistics_Composed.mp
Traces:  (none provided)
States:  36  Orderings: 4  REJECTs: 12

Total candidate findings: 7
  Shape A: 4
  Shape B: 3
  Shape C: 0

### Shape A -- vacuous-foreach gaps

A1. Ordering 'vhf_ch16_broadcast BEFORE planning_evasive_maneuver' is vacuously satisfiable when colregs_give_way is active but vts_issuing_warning is absent. No REJECT enforces colregs_give_way -> (vts_issuing_warning).
    Suggested REJECT:
        IF #colregs_give_way > 0 AND #vts_issuing_warning == 0 THEN REJECT; FI;

A2. Ordering 'transiting_to_vessel BEFORE pushing_pulling' is vacuously satisfiable when tugs_assisting is active but tugs_dispatched is absent. No REJECT enforces tugs_assisting -> (tugs_dispatched).
    Suggested REJECT:
        IF #tugs_assisting > 0 AND #tugs_dispatched == 0 THEN REJECT; FI;

A3. Ordering 'schedule_confirmed BEFORE lines_fast' is vacuously satisfiable when vessel_moored is active but berth_allocated is absent. No REJECT enforces vessel_moored -> (berth_allocated).
    Suggested REJECT:
        IF #vessel_moored > 0 AND #berth_allocated == 0 THEN REJECT; FI;

A4. Ordering 'planning_evasive_maneuver BEFORE rudder_commanded' is vacuously satisfiable when vessel_altering_course is active but colregs_give_way is absent. No REJECT enforces vessel_altering_course -> (colregs_give_way).
    Suggested REJECT:
        IF #vessel_altering_course > 0 AND #colregs_give_way == 0 THEN REJECT; FI;

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'cargo_ops_active requires (berth_occupied)'. ais_tx_rx_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #ais_tx_rx_active > 0 AND #berth_occupied == 0 THEN REJECT; FI;

B2. Schema has rule 'cargo_ops_active requires (vessel_moored)'. ais_tx_rx_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #ais_tx_rx_active > 0 AND #vessel_moored == 0 THEN REJECT; FI;

B3. Schema has rule 'colregs_give_way requires (vessel_altering_course | vessel_stopping)'. colregs_stand_on (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #colregs_stand_on > 0 AND #vessel_altering_course == 0 AND #vessel_stopping == 0 THEN REJECT; FI;

### Shape C -- optional-event escalation

(no candidates)
