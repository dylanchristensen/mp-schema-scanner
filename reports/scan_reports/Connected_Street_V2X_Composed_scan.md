## INSuRE+C Schema Scanner

Schema:  D:\Research\NSA INSuRE+C\Summer\Models + Writeups\Smart Street\Connected_Street_V2X_Composed.mp
Traces:  (none provided)
States:  32  Orderings: 6  REJECTs: 12

Total candidate findings: 7
  Shape A: 0
  Shape B: 7
  Shape C: 0

### Shape A -- vacuous-foreach gaps

(no candidates)

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'tc_preempt_active requires (ev_responding)'. obu_tx_rx_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #obu_tx_rx_active > 0 AND #ev_responding == 0 THEN REJECT; FI;

B2. Schema has rule 'tc_preempt_active requires (ev_responding)'. overlap_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #overlap_active > 0 AND #ev_responding == 0 THEN REJECT; FI;

B3. Schema has rule 'tc_preempt_active requires (ev_responding)'. vru_crossing_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #vru_crossing_active > 0 AND #ev_responding == 0 THEN REJECT; FI;

B4. Schema has rule 'av_braking_emergency requires (collision_predicted)'. av_braking_normal (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #av_braking_normal > 0 AND #collision_predicted == 0 THEN REJECT; FI;

B5. Schema has rule 'tc_preempt_active requires (ev_responding)'. tc_coord_normal (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #tc_coord_normal > 0 AND #ev_responding == 0 THEN REJECT; FI;

B6. Schema has rule 'tc_preempt_active requires (ev_responding)'. tc_flash_fault (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #tc_flash_fault > 0 AND #ev_responding == 0 THEN REJECT; FI;

B7. Schema has rule 'tc_preempt_active requires (ev_responding)'. tc_transit_priority (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #tc_transit_priority > 0 AND #ev_responding == 0 THEN REJECT; FI;

### Shape C -- optional-event escalation

(no candidates)
