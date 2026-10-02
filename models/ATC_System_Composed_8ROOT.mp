/* ═══════════════════════════════════════════════════════════════
   Air Traffic Control System — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Composed 8-ROOT model of a terminal/en-route ATC system.
   Grounded in real protocols and documentation:

   Sources:
     - ICAO Doc 4444 (PANS-ATM, 16th Ed.): ATC procedures,
       separation, clearance, handoff, flight plan processing
     - ICAO Doc 9854: Global ATM Operational Concept
     - FAA Order 7110.65 (ATC): Controller procedures for
       clearance delivery, ground, local, departure, approach
     - FAA NAS Enterprise Architecture: ERAM, STARS, TFMS,
       TBFM, TFDM facility decomposition
     - EUROCONTROL ASTERIX: CAT048 (SSR/Mode-S), CAT021 (ADS-B),
       CAT062 (system tracks) surveillance data formats
     - ICAO Annex 10 Vol IV: CPDLC message set (uplink/downlink)
     - DO-185B / ICAO Doc 9863: ACAS/TCAS II logic (TA/RA)
     - SAE J1772, RTCA DO-260B: ADS-B transponder standards
     - FAA SWIM: System Wide Information Management SOA

   Components (map to real NAS elements):
     - Aircraft            -- Airframe + avionics (transponder, FMS, TCAS)
     - Tower_Control       -- ATCT: Clearance Delivery + Ground + Local
     - TRACON              -- Terminal radar: Departure + Approach control
     - ARTCC               -- En-route center: sector control (ERAM)
     - Surveillance_System -- SSR/Mode-S, PSR, ADS-B, MLAT sensors
     - Comm_System         -- VHF/UHF voice + CPDLC data link
     - Flow_Management     -- ATCSCC + TFMS + TBFM national flow
     - Weather_System      -- ITWS, TDWR, NEXRAD, ATIS/D-ATIS
═══════════════════════════════════════════════════════════════ */

SCHEMA ATC_System_Composed


/* ═══════════════════════════════════════════
   ROOT COMPONENTS
   Each represents one system in the SoS.
═══════════════════════════════════════════ */

ROOT Aircraft :
    ( ac_parked_at_gate  | ac_taxi_out    | ac_holding_short
    | ac_takeoff_roll    | ac_departure   | ac_en_route
    | ac_arrival_descent | ac_final_approach | ac_landing_roll
    | ac_taxi_in         | ac_holding_pattern | ac_diverting
    | ac_emergency );

ROOT Tower_Control :
    ( twr_clearance_delivery | twr_ground_control
    | twr_local_control      | twr_combined_position
    | twr_closed );

ROOT TRACON :
    ( tracon_departure_active | tracon_approach_active
    | tracon_combined_ops     | tracon_saturated
    | tracon_offline );

ROOT ARTCC :
    ( center_sector_active  | center_sector_combined
    | center_flow_restricted | center_adsb_only
    | center_offline );

ROOT Surveillance_System :
    ( surv_full_coverage    | surv_degraded_psr_only
    | surv_degraded_ssr_only | surv_adsb_only
    | surv_no_coverage );

ROOT Comm_System :
    ( comm_voice_and_cpdlc | comm_voice_only
    | comm_cpdlc_only      | comm_backup_frequency
    | comm_total_failure );

ROOT Flow_Management :
    ( flow_normal       | flow_mit_applied
    | flow_gdp_active   | flow_gs_active
    | flow_afp_active   | flow_edct_assigned );

ROOT Weather_System :
    ( wx_vmc_conditions  | wx_imc_conditions
    | wx_convective_sigmet | wx_windshear_alert
    | wx_low_visibility_ops );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
   Internal events within each state.
   Based on real protocol actions/messages.
═══════════════════════════════════════════ */

/* --- Aircraft ---
   States from ICAO Doc 4444 flight phases.
   Sub-events reference real avionics actions. */

ac_parked_at_gate :
    atis_received
    fpl_filed;

ac_taxi_out :
    squawk_assigned
    taxi_clearance_received;

ac_holding_short :
    awaiting_lineup_clearance;

ac_takeoff_roll :
    takeoff_clearance_received
    transponder_mode_s_active;

ac_departure :
    airborne
    sid_following
    initial_climb;

ac_en_route :
    airborne
    flight_level_assigned
    position_reporting;

ac_arrival_descent :
    airborne
    star_following
    descending;

ac_final_approach :
    airborne
    approach_clearance_received
    localizer_captured;

ac_landing_roll :
    on_runway
    speed_decelerating;

ac_taxi_in :
    taxi_clearance_received
    squawk_standby;

ac_holding_pattern :
    airborne
    holding_clearance_received
    expect_further_clearance;

ac_diverting :
    airborne
    diversion_clearance;

ac_emergency :
    squawk_7700
    [tcas_ra_active];

/* --- Tower Control ---
   FAA 7110.65: ATCT positions.
   Real controller positions and responsibilities. */

twr_clearance_delivery :
    issuing_ifr_clearance
    assigning_squawk_code
    assigning_departure_frequency;

twr_ground_control :
    issuing_taxi_instructions
    monitoring_surface_movement
    coordinating_runway_crossing;

twr_local_control :
    issuing_takeoff_clearance
    issuing_landing_clearance
    sequencing_traffic
    scanning_final;

twr_combined_position :
    issuing_taxi_instructions
    issuing_takeoff_clearance
    issuing_landing_clearance;

twr_closed : ;

/* --- TRACON ---
   FAA STARS (Standard Terminal Automation Replacement System).
   Real departure/approach control functions. */

tracon_departure_active :
    radar_contact_established
    issuing_climb_clearance
    vectoring_to_airway
    handoff_to_center;

tracon_approach_active :
    receiving_handoff_from_center
    issuing_descent_clearance
    sequencing_arrivals
    vectoring_to_final;

tracon_combined_ops :
    radar_contact_established
    sequencing_arrivals
    vectoring_to_airway;

tracon_saturated :
    sequencing_arrivals
    workload_exceeded;

tracon_offline : ;

/* --- ARTCC ---
   FAA ERAM (En Route Automation Modernization).
   Real en-route center operations per ICAO Doc 4444. */

center_sector_active :
    providing_separation
    issuing_flight_level_changes
    processing_handoffs
    conflict_detection_active;

center_sector_combined :
    providing_separation
    processing_handoffs;

center_flow_restricted :
    providing_separation
    miles_in_trail_enforced;

center_adsb_only :
    adsb_surveillance_only
    providing_separation;

center_offline : ;

/* --- Surveillance System ---
   EUROCONTROL ASTERIX categories.
   Real sensor types per ICAO Annex 10. */

surv_full_coverage :
    psr_operational
    ssr_mode_s_operational
    adsb_receiving
    asterix_cat048_transmitting
    asterix_cat021_transmitting
    system_track_cat062;

surv_degraded_psr_only :
    psr_operational
    asterix_cat048_transmitting;

surv_degraded_ssr_only :
    ssr_mode_s_operational
    asterix_cat048_transmitting;

surv_adsb_only :
    adsb_receiving
    asterix_cat021_transmitting;

surv_no_coverage : ;

/* --- Communication System ---
   ICAO Annex 10 Vol III/IV.
   VHF voice + CPDLC data link states. */

comm_voice_and_cpdlc :
    vhf_transmitting
    cpdlc_uplink_active
    cpdlc_downlink_active;

comm_voice_only :
    vhf_transmitting;

comm_cpdlc_only :
    cpdlc_uplink_active
    cpdlc_downlink_active;

comm_backup_frequency :
    backup_vhf_active;

comm_total_failure : ;

/* --- Flow Management ---
   FAA TFMS/TBFM + ATCSCC programs.
   Real traffic management initiatives (TMIs). */

flow_normal :
    tfms_monitoring
    tbfm_scheduling;

flow_mit_applied :
    tfms_monitoring
    miles_in_trail_published;

flow_gdp_active :
    ground_delay_program
    edct_times_computed
    swim_publishing;

flow_gs_active :
    ground_stop_issued
    departures_halted;

flow_afp_active :
    airspace_flow_program
    reroutes_published;

flow_edct_assigned :
    tfms_monitoring
    edct_times_computed;

/* --- Weather System ---
   FAA ITWS, TDWR, NWS products.
   Real meteorological states per METAR/TAF/SIGMET. */

wx_vmc_conditions :
    metar_reporting
    ceiling_above_minimums
    visibility_above_minimums;

wx_imc_conditions :
    metar_reporting
    ceiling_below_vfr
    instrument_approaches_required;

wx_convective_sigmet :
    metar_reporting
    sigmet_issued
    convective_cells_detected;

wx_windshear_alert :
    metar_reporting
    tdwr_alert_active
    pirep_windshear;

wx_low_visibility_ops :
    metar_reporting
    rvr_reporting
    cat_ii_iii_procedures;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
   Based on real procedural sequences from
   ICAO Doc 4444 and FAA Order 7110.65.
═══════════════════════════════════════════ */

/* ICAO 4444 §4.5: IFR clearance must be delivered
   before squawk code is activated for departure. */
ENSURE FOREACH $c: issuing_ifr_clearance, $s: squawk_assigned
    ($c BEFORE $s);

/* ICAO 4444 §7.6: Radar contact must be established
   before issuing radar-based climb clearance. */
ENSURE FOREACH $r: radar_contact_established, $c: issuing_climb_clearance
    ($r BEFORE $c);

/* FAA 7110.65 §5-8: ARTCC conflict detection must
   precede flight level change instructions. */
ENSURE FOREACH $d: conflict_detection_active, $f: issuing_flight_level_changes
    ($d BEFORE $f);

/* ICAO 4444 §6.5: Approach clearance precedes
   localizer capture (ILS establishment). */
ENSURE FOREACH $a: approach_clearance_received, $l: localizer_captured
    ($a BEFORE $l);

/* FAA TFMS: EDCT computation must precede GDP
   ground delay assignment. */
ENSURE FOREACH $e: edct_times_computed, $g: ground_delay_program
    ($e BEFORE $g);

/* EUROCONTROL ASTERIX: Raw sensor data (CAT048/021)
   must be available before system tracks (CAT062). */
ENSURE FOREACH $r: asterix_cat048_transmitting, $s: system_track_cat062
    ($r BEFORE $s);

ENSURE FOREACH $a: asterix_cat021_transmitting, $s: system_track_cat062
    ($a BEFORE $s);

/* ICAO Annex 10 Vol IV: CPDLC downlink (pilot response)
   follows uplink (controller instruction). */
ENSURE FOREACH $u: cpdlc_uplink_active, $d: cpdlc_downlink_active
    ($u BEFORE $d);

/* NWS/FAA: TDWR alert must precede windshear PIREPs
   in temporal ordering (alert triggers reporting). */
ENSURE FOREACH $t: tdwr_alert_active, $p: pirep_windshear
    ($t BEFORE $p);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
   Hard physical/logical/regulatory constraints.
   Each cites its regulatory basis.
═══════════════════════════════════════════ */

/* ------- Surveillance dependencies ------- */

/* ICAO Doc 4444 §8.1: Radar separation requires
   surveillance coverage. No coverage = no radar service. */
IF #providing_separation > 0
    AND #surv_no_coverage > 0 THEN
    REJECT;
FI;

/* EUROCONTROL ASTERIX: Mode-S interrogation requires SSR.
   Transponder Mode-S active needs SSR or ADS-B receiving. */
IF #transponder_mode_s_active > 0
    AND #ssr_mode_s_operational == 0
    AND #adsb_receiving == 0 THEN
    REJECT;
FI;

/* ADS-B-only center ops require ADS-B receiver online. */
IF #center_adsb_only > 0 AND #adsb_receiving == 0 THEN
    REJECT;
FI;

/* ------- Communication dependencies ------- */

/* ICAO Doc 4444 §3.6: ATC clearances require
   two-way communication. Total comm failure = no clearance. */
IF #issuing_ifr_clearance > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

IF #issuing_takeoff_clearance > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

IF #issuing_landing_clearance > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

IF #issuing_climb_clearance > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

IF #issuing_descent_clearance > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

/* CPDLC requires functioning data link (ICAO Annex 10 Vol IV). */
IF #cpdlc_uplink_active > 0
    AND #comm_voice_and_cpdlc == 0
    AND #comm_cpdlc_only == 0 THEN
    REJECT;
FI;

/* ------- Flow management dependencies ------- */

/* FAA ATCSCC: Ground stop halts all departures.
   Takeoff clearance cannot be issued during GS. */
IF #flow_gs_active > 0 AND #issuing_takeoff_clearance > 0 THEN
    REJECT;
FI;

/* FAA TFMS: GDP requires SWIM data publishing. */
IF #flow_gdp_active > 0 AND #swim_publishing == 0 THEN
    REJECT;
FI;

/* MIT in flow management must be matched at ARTCC level. */
IF #flow_mit_applied > 0 AND #miles_in_trail_enforced == 0 THEN
    REJECT;
FI;

/* ------- Weather dependencies ------- */

/* FAA 7110.65 §2-6: Low visibility operations
   require RVR reporting equipment active. */
IF #wx_low_visibility_ops > 0 AND #rvr_reporting == 0 THEN
    REJECT;
FI;

/* CAT II/III approaches require ILS and low-vis procedure.
   Localizer capture during low-vis needs CAT II/III. */
IF #localizer_captured > 0
    AND #wx_low_visibility_ops > 0
    AND #cat_ii_iii_procedures == 0 THEN
    REJECT;
FI;

/* Convective SIGMET with ground stop should not have departures. */
IF #wx_convective_sigmet > 0
    AND #flow_gs_active > 0
    AND #ac_takeoff_roll > 0 THEN
    REJECT;
FI;

/* ------- TCAS/ACAS constraints ------- */

/* ICAO Doc 9863 / DO-185B: TCAS RA activation requires
   airborne state — only active in flight. */
IF #tcas_ra_active > 0 AND #airborne == 0 THEN
    REJECT;
FI;

/* Emergency squawk 7700 requires either comm failure
   or explicit emergency declaration — aircraft must
   be in ac_emergency state. */
IF #squawk_7700 > 0 AND #ac_emergency == 0 THEN
    REJECT;
FI;

/* ------- Facility operational constraints ------- */

/* Tower closed = no ground or local control available. */
IF #twr_closed > 0 AND #issuing_taxi_instructions > 0 THEN
    REJECT;
FI;

IF #twr_closed > 0 AND #issuing_takeoff_clearance > 0 THEN
    REJECT;
FI;

IF #twr_closed > 0 AND #issuing_landing_clearance > 0 THEN
    REJECT;
FI;

/* TRACON offline = no radar vectors or sequencing. */
IF #tracon_offline > 0 AND #vectoring_to_final > 0 THEN
    REJECT;
FI;

IF #tracon_offline > 0 AND #vectoring_to_airway > 0 THEN
    REJECT;
FI;

/* ARTCC offline = no en-route separation service. */
IF #center_offline > 0 AND #providing_separation > 0 THEN
    REJECT;
FI;

/* Aircraft cannot be airborne with tower closed AND
   TRACON offline AND center offline (no ATC anywhere). */
IF #airborne > 0
    AND #twr_closed > 0
    AND #tracon_offline > 0
    AND #center_offline > 0 THEN
    REJECT;
FI;

/* ------- Handoff protocol constraints ------- */

/* ICAO 4444 §3.3.2: Handoff to center requires
   TRACON departure to initiate it. */
IF #handoff_to_center > 0
    AND #tracon_departure_active == 0
    AND #tracon_combined_ops == 0 THEN
    REJECT;
FI;

/* Receiving handoff from center requires center active. */
IF #receiving_handoff_from_center > 0
    AND #center_sector_active == 0
    AND #center_sector_combined == 0
    AND #center_flow_restricted == 0
    AND #center_adsb_only == 0 THEN
    REJECT;
FI;

/* Processing handoffs at ARTCC requires comm link. */
IF #processing_handoffs > 0 AND #comm_total_failure > 0 THEN
    REJECT;
FI;

/* Holding pattern requires explicit clearance from ATC.
   Cannot hold if no ATC facility is issuing clearances. */
IF #ac_holding_pattern > 0
    AND #issuing_ifr_clearance == 0
    AND #issuing_climb_clearance == 0
    AND #issuing_descent_clearance == 0
    AND #sequencing_arrivals == 0 THEN
    REJECT;
FI;


/* ═══════════════════════════════════════════
   COORDINATION (PRECEDES)
   Information flow between systems.
   Based on real data exchange protocols.
═══════════════════════════════════════════ */

/* Surveillance → ARTCC: ASTERIX system tracks feed
   ERAM conflict detection (CAT062 → ERAM). */
IF #system_track_cat062 > 0 AND #conflict_detection_active > 0 THEN
    COORDINATE $s : system_track_cat062     FROM Surveillance_System,
               $c : conflict_detection_active FROM ARTCC
        DO ADD $s PRECEDES $c; OD;
FI;

/* Surveillance → TRACON: Radar data feeds STARS
   sequencing (ASTERIX → STARS). */
IF #asterix_cat048_transmitting > 0 AND #sequencing_arrivals > 0 THEN
    COORDINATE $r : asterix_cat048_transmitting FROM Surveillance_System,
               $s : sequencing_arrivals          FROM TRACON
        DO ADD $r PRECEDES $s; OD;
FI;

/* Flow Management → Tower: Ground stop halts departures
   (TFMS → TFDM → Tower). */
IF #ground_stop_issued > 0 AND #twr_clearance_delivery > 0 THEN
    COORDINATE $g : ground_stop_issued     FROM Flow_Management,
               $t : issuing_ifr_clearance  FROM Tower_Control
        DO ADD $g PRECEDES $t; OD;
FI;

/* Weather → Flow Management: SIGMET triggers TMI
   (NWS → ATCSCC → TFMS). */
IF #sigmet_issued > 0 AND #flow_gdp_active > 0 THEN
    COORDINATE $w : sigmet_issued        FROM Weather_System,
               $f : ground_delay_program FROM Flow_Management
        DO ADD $w PRECEDES $f; OD;
FI;

IF #sigmet_issued > 0 AND #flow_gs_active > 0 THEN
    COORDINATE $w : sigmet_issued      FROM Weather_System,
               $f : ground_stop_issued FROM Flow_Management
        DO ADD $w PRECEDES $f; OD;
FI;

/* Weather → Tower: Windshear alert affects local control
   (TDWR → ATCT). */
IF #tdwr_alert_active > 0 AND #scanning_final > 0 THEN
    COORDINATE $w : tdwr_alert_active FROM Weather_System,
               $t : scanning_final    FROM Tower_Control
        DO ADD $w PRECEDES $t; OD;
FI;

/* Comm → ARTCC: Voice/CPDLC enables controller instructions
   (VHF/CPDLC → ERAM workstation). */
IF #vhf_transmitting > 0 AND #providing_separation > 0 THEN
    COORDINATE $c : vhf_transmitting     FROM Comm_System,
               $a : providing_separation FROM ARTCC
        DO ADD $c PRECEDES $a; OD;
FI;
