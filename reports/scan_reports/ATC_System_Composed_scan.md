## INSuRE+C Schema Scanner

Schema:  D:\Research\NSA INSuRE+C\Summer\Models + Writeups\ATC\ATC_System_Composed.mp
Traces:  (none provided)
States:  49  Orderings: 9  REJECTs: 28

Total candidate findings: 52
  Shape A: 4
  Shape B: 47
  Shape C: 1

### Shape A -- vacuous-foreach gaps

A1. Ordering 'issuing_ifr_clearance BEFORE squawk_assigned' is vacuously satisfiable when ac_taxi_out is active but twr_clearance_delivery is absent. No REJECT enforces ac_taxi_out -> (twr_clearance_delivery).
    Suggested REJECT:
        IF #ac_taxi_out > 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

A2. Ordering 'edct_times_computed BEFORE ground_delay_program' is vacuously satisfiable when flow_gdp_active is active but flow_edct_assigned is absent. No REJECT enforces flow_gdp_active -> (flow_edct_assigned).
    Suggested REJECT:
        IF #flow_gdp_active > 0 AND #flow_edct_assigned == 0 THEN REJECT; FI;

A3. Ordering 'asterix_cat048_transmitting BEFORE system_track_cat062' is vacuously satisfiable when surv_full_coverage is active but surv_degraded_ssr_only is absent. No REJECT enforces surv_full_coverage -> (surv_adsb_only | surv_degraded_ssr_only).
    Suggested REJECT:
        IF #surv_full_coverage > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

A4. Ordering 'asterix_cat021_transmitting BEFORE system_track_cat062' is vacuously satisfiable when surv_full_coverage is active but surv_adsb_only is absent. No REJECT enforces surv_full_coverage -> (surv_adsb_only | surv_degraded_ssr_only).
    Suggested REJECT:
        IF #surv_full_coverage > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'tracon_departure_active requires (tracon_combined_ops | tracon_departure_active)'. ac_departure (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_departure > 0 AND #tracon_combined_ops == 0 AND #tracon_departure_active == 0 THEN REJECT; FI;

B2. Schema has rule 'tracon_approach_active requires (center_adsb_only | center_flow_restricted | center_sector_active | center_sector_combined)'. ac_final_approach (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_final_approach > 0 AND #center_adsb_only == 0 AND #center_flow_restricted == 0 AND #center_sector_active == 0 AND #center_sector_combined == 0 THEN REJECT; FI;

B3. Schema has rule 'comm_cpdlc_only requires (comm_cpdlc_only | comm_voice_and_cpdlc)'. center_adsb_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_adsb_only > 0 AND #comm_cpdlc_only == 0 AND #comm_voice_and_cpdlc == 0 THEN REJECT; FI;

B4. Schema has rule 'flow_gdp_active requires (flow_gdp_active)'. center_sector_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_sector_active > 0 AND #flow_gdp_active == 0 THEN REJECT; FI;

B5. Schema has rule 'tracon_departure_active requires (tracon_combined_ops | tracon_departure_active)'. center_sector_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_sector_active > 0 AND #tracon_combined_ops == 0 AND #tracon_departure_active == 0 THEN REJECT; FI;

B6. Schema has rule 'center_adsb_only requires (surv_adsb_only)'. comm_cpdlc_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #comm_cpdlc_only > 0 AND #surv_adsb_only == 0 THEN REJECT; FI;

B7. Schema has rule 'center_adsb_only requires (surv_adsb_only)'. comm_voice_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #comm_voice_only > 0 AND #surv_adsb_only == 0 THEN REJECT; FI;

B8. Schema has rule 'tracon_departure_active requires (tracon_combined_ops | tracon_departure_active)'. flow_afp_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_afp_active > 0 AND #tracon_combined_ops == 0 AND #tracon_departure_active == 0 THEN REJECT; FI;

B9. Schema has rule 'tracon_approach_active requires (center_adsb_only | center_flow_restricted | center_sector_active | center_sector_combined)'. flow_afp_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_afp_active > 0 AND #center_adsb_only == 0 AND #center_flow_restricted == 0 AND #center_sector_active == 0 AND #center_sector_combined == 0 THEN REJECT; FI;

B10. Schema has rule 'tracon_departure_active requires (tracon_combined_ops | tracon_departure_active)'. flow_gdp_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_gdp_active > 0 AND #tracon_combined_ops == 0 AND #tracon_departure_active == 0 THEN REJECT; FI;

B11. Schema has rule 'tracon_approach_active requires (center_adsb_only | center_flow_restricted | center_sector_active | center_sector_combined)'. flow_gdp_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_gdp_active > 0 AND #center_adsb_only == 0 AND #center_flow_restricted == 0 AND #center_sector_active == 0 AND #center_sector_combined == 0 THEN REJECT; FI;

B12. Schema has rule 'tracon_departure_active requires (tracon_combined_ops | tracon_departure_active)'. flow_gs_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_gs_active > 0 AND #tracon_combined_ops == 0 AND #tracon_departure_active == 0 THEN REJECT; FI;

B13. Schema has rule 'tracon_approach_active requires (center_adsb_only | center_flow_restricted | center_sector_active | center_sector_combined)'. flow_gs_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #flow_gs_active > 0 AND #center_adsb_only == 0 AND #center_flow_restricted == 0 AND #center_sector_active == 0 AND #center_sector_combined == 0 THEN REJECT; FI;

B14. Schema has rule 'comm_cpdlc_only requires (comm_cpdlc_only | comm_voice_and_cpdlc)'. surv_adsb_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #surv_adsb_only > 0 AND #comm_cpdlc_only == 0 AND #comm_voice_and_cpdlc == 0 THEN REJECT; FI;

B15. Schema has rule 'comm_cpdlc_only requires (comm_cpdlc_only | comm_voice_and_cpdlc)'. surv_degraded_psr_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #surv_degraded_psr_only > 0 AND #comm_cpdlc_only == 0 AND #comm_voice_and_cpdlc == 0 THEN REJECT; FI;

B16. Schema has rule 'comm_cpdlc_only requires (comm_cpdlc_only | comm_voice_and_cpdlc)'. surv_degraded_ssr_only (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #surv_degraded_ssr_only > 0 AND #comm_cpdlc_only == 0 AND #comm_voice_and_cpdlc == 0 THEN REJECT; FI;

B17. Schema has rule 'flow_gdp_active requires (flow_gdp_active)'. tracon_approach_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #tracon_approach_active > 0 AND #flow_gdp_active == 0 THEN REJECT; FI;

B18. Schema has rule 'wx_low_visibility_ops requires (wx_low_visibility_ops)'. tracon_combined_ops (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #tracon_combined_ops > 0 AND #wx_low_visibility_ops == 0 THEN REJECT; FI;

B19. Schema has rule 'flow_gdp_active requires (flow_gdp_active)'. tracon_departure_active (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #tracon_departure_active > 0 AND #flow_gdp_active == 0 THEN REJECT; FI;

B20. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_arrival_descent (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_arrival_descent > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B21. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_arrival_descent (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_arrival_descent > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B22. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_departure (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_departure > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B23. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_departure (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_departure > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B24. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_diverting (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_diverting > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B25. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_diverting (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_diverting > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B26. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_emergency (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_emergency > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B27. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_emergency (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_emergency > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B28. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_en_route (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_en_route > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B29. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_en_route (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_en_route > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B30. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_final_approach (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_final_approach > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B31. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_final_approach (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_final_approach > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B32. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_holding_pattern (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_holding_pattern > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B33. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_holding_short (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_holding_short > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B34. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_holding_short (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_holding_short > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B35. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_landing_roll (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_landing_roll > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B36. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_landing_roll (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_landing_roll > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B37. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_parked_at_gate (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_parked_at_gate > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B38. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_parked_at_gate (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_parked_at_gate > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B39. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_takeoff_roll (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_takeoff_roll > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B40. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_taxi_in (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_taxi_in > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B41. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_taxi_in (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_taxi_in > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B42. Schema has rule 'ac_takeoff_roll requires (surv_adsb_only | surv_degraded_ssr_only)'. ac_taxi_out (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_taxi_out > 0 AND #surv_adsb_only == 0 AND #surv_degraded_ssr_only == 0 THEN REJECT; FI;

B43. Schema has rule 'ac_holding_pattern requires (tracon_approach_active | tracon_departure_active | tracon_saturated | twr_clearance_delivery)'. ac_taxi_out (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #ac_taxi_out > 0 AND #tracon_approach_active == 0 AND #tracon_departure_active == 0 AND #tracon_saturated == 0 AND #twr_clearance_delivery == 0 THEN REJECT; FI;

B44. Schema has rule 'center_adsb_only requires (surv_adsb_only)'. center_flow_restricted (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_flow_restricted > 0 AND #surv_adsb_only == 0 THEN REJECT; FI;

B45. Schema has rule 'center_adsb_only requires (surv_adsb_only)'. center_sector_active (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_sector_active > 0 AND #surv_adsb_only == 0 THEN REJECT; FI;

B46. Schema has rule 'center_adsb_only requires (surv_adsb_only)'. center_sector_combined (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #center_sector_combined > 0 AND #surv_adsb_only == 0 THEN REJECT; FI;

B47. Schema has rule 'tracon_approach_active requires (center_adsb_only | center_flow_restricted | center_sector_active | center_sector_combined)'. tracon_departure_active (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #tracon_departure_active > 0 AND #center_adsb_only == 0 AND #center_flow_restricted == 0 AND #center_sector_active == 0 AND #center_sector_combined == 0 THEN REJECT; FI;

### Shape C -- optional-event escalation

C1. REJECT triggered by optional event 'tcas_ra_active' of state 'ac_emergency'. When 'tcas_ra_active' does not fire, 'ac_emergency' can be active without requiring (ac_diverting). Escalating to parent state closes this gap.
    Suggested REJECT:
        IF #ac_emergency > 0 AND #ac_diverting == 0 THEN REJECT; FI;
