/* ═══════════════════════════════════════════════════════════════
   Global Maritime Tracking and Port Logistics — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Composed 8-ROOT model of a Maritime/Port Ecosystem.
   Grounded in real maritime protocols and navigation laws.

   Sources:
     - ITU-R M.1371: Automatic Identification System (AIS)
       Class A dynamic/static/voyage message types.
     - IMO COLREGs: International Regulations for Preventing
       Collisions at Sea (Rules 16/17 Stand-on/Give-way).
     - IALA VTS Manual: Vessel Traffic Service operations.
     - NMEA 0183/2000: Shipboard sensor networks (GNSS to ECDIS).

   Components:
     - Vessel_Kinematics  -- Physical motion of a large cargo vessel
     - Vessel_Navigation  -- Bridge decision logic (COLREGs, ECDIS)
     - Vessel_AIS         -- VHF transponder (Dynamic/Static MSGs)
     - VTS_Center         -- Shore-based traffic management
     - Port_Terminal      -- Physical berth and automated cranes
     - Tugboat_Fleet      -- Harbor assist vessels
     - Weather_Tide       -- Meteorological and hydrological state
     - GNSS_System        -- GPS/GLONASS satellite constellation
═══════════════════════════════════════════════════════════════ */

SCHEMA Maritime_Port_Logistics_Composed

/* ═══════════════════════════════════════════
   ROOT COMPONENTS
═══════════════════════════════════════════ */

ROOT Vessel_Kinematics :
    ( vessel_cruising | vessel_altering_course | vessel_stopping
    | vessel_maneuvering_port | vessel_moored | vessel_anchored );

ROOT Vessel_Navigation :
    ( ecdis_nominal | colregs_stand_on | colregs_give_way
    | pilot_onboard | nav_degraded );

ROOT Vessel_AIS :
    ( ais_tx_rx_active | ais_rx_only
    | ais_transmitting_error | ais_offline );

ROOT VTS_Center :
    ( vts_monitoring | vts_issuing_warning
    | vts_managing_anchorage | vts_offline );

ROOT Port_Terminal :
    ( berth_available | berth_allocated | berth_occupied
    | cargo_ops_active | terminal_congested );

ROOT Tugboat_Fleet :
    ( tugs_idle | tugs_dispatched | tugs_assisting
    | tugs_unavailable );

ROOT Weather_Tide :
    ( weather_nominal | restricted_visibility | storm_gale
    | tide_high | tide_low );

ROOT GNSS_System :
    ( gnss_nominal | gnss_degraded | gnss_jammed );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
═══════════════════════════════════════════ */

/* --- Vessel Kinematics --- */
vessel_cruising :
    maintaining_speed_and_heading;

vessel_altering_course :
    rudder_commanded
    heading_changing;

vessel_stopping :
    engine_astern
    speed_dropping;

vessel_maneuvering_port :
    engine_dead_slow
    bow_thrusters_active;

vessel_moored :
    lines_fast
    engine_finished;

vessel_anchored :
    anchor_dropped
    holding_position;

/* --- Vessel Navigation (Bridge) --- */
ecdis_nominal :
    route_monitoring
    radar_arpa_tracking;

colregs_stand_on :
    Rule_17_maintain_course_speed
    [Rule_17_action_in_extremis];

colregs_give_way :
    Rule_16_take_early_action
    planning_evasive_maneuver;

pilot_onboard :
    master_pilot_exchange
    local_knowledge_applied;

nav_degraded :
    manual_plotting_required
    visual_lookout_enhanced;

/* --- Vessel AIS --- */
ais_tx_rx_active :
    tx_msg1_dynamic       /* Position, COG, SOG */
    tx_msg5_static        /* Ship name, dimensions, ETA */
    rx_target_reports;

ais_rx_only :
    rx_target_reports
    tx_suppressed;

ais_transmitting_error :
    tx_msg1_dynamic       /* Transmitting, but bad data */
    heading_sensor_unreliable;

ais_offline :
    no_rf_transmission;

/* --- VTS Center --- */
vts_monitoring :
    radar_overlay_active
    ais_ingestion;

vts_issuing_warning :
    vhf_ch16_broadcast
    conflict_identified;

vts_managing_anchorage :
    assigning_anchorage_berth
    monitoring_drag;

vts_offline :
    shore_radar_down;

/* --- Port Terminal --- */
berth_available :
    ready_for_arrival;

berth_allocated :
    schedule_confirmed;

berth_occupied :
    vessel_alongside;

cargo_ops_active :
    sts_cranes_working
    agvs_routing;

terminal_congested :
    berths_full
    vessels_delayed;

/* --- Tugboat Fleet --- */
tugs_idle :
    on_standby;

tugs_dispatched :
    transiting_to_vessel;

tugs_assisting :
    lines_made_fast
    pushing_pulling;

tugs_unavailable :
    all_tugs_committed;

/* --- Weather Tide --- */
weather_nominal :
    good_visibility;

restricted_visibility :
    fog_bank
    Rule_19_applies;

storm_gale :
    high_winds
    rough_seas;

tide_high :
    max_under_keel_clearance;

tide_low :
    min_under_keel_clearance;

/* --- GNSS System --- */
gnss_nominal :
    precise_position_fix;

gnss_degraded :
    high_hdop;

gnss_jammed :
    loss_of_position;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
═══════════════════════════════════════════ */

/* VTS warning precedes an evasive maneuver. */
ENSURE FOREACH $w: vhf_ch16_broadcast, $e: planning_evasive_maneuver
    ($w BEFORE $e);

/* Tugs must be dispatched before assisting. */
ENSURE FOREACH $d: transiting_to_vessel, $a: pushing_pulling
    ($d BEFORE $a);

/* Berth must be allocated before a vessel can moor. */
ENSURE FOREACH $a: schedule_confirmed, $m: lines_fast
    ($a BEFORE $m);

/* COLREGs: Give-way planning precedes altering course. */
ENSURE FOREACH $p: planning_evasive_maneuver, $r: rudder_commanded
    ($p BEFORE $r);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
═══════════════════════════════════════════ */

/* COLREGs Rule 16: Give-way vessel MUST take action.
   It cannot maintain cruising without altering course or stopping. */
IF #colregs_give_way > 0
    AND #vessel_altering_course == 0
    AND #vessel_stopping == 0 THEN
    REJECT;
FI;

/* COLREGs Rule 17: Stand-on vessel MUST maintain course/speed initially. */
IF #colregs_stand_on > 0
    AND #vessel_altering_course > 0
    AND #Rule_17_action_in_extremis == 0 THEN
    REJECT;
FI;

/* Port maneuvers require a pilot. */
IF #vessel_maneuvering_port > 0 AND #pilot_onboard == 0 THEN
    REJECT;
FI;

/* Large cargo vessels require tugs to moor. */
IF #vessel_moored > 0 AND #tugs_assisting == 0 THEN
    REJECT;
FI;

/* Cannot moor if terminal is congested and berths are full. */
IF #vessel_moored > 0 AND #terminal_congested > 0 THEN
    REJECT;
FI;

/* Cargo operations only happen when a vessel is moored and berth is occupied. */
IF #cargo_ops_active > 0 AND #berth_occupied == 0 THEN
    REJECT;
FI;
IF #cargo_ops_active > 0 AND #vessel_moored == 0 THEN
    REJECT;
FI;

/* AIS dynamic messages (Position) require GNSS. */
IF #tx_msg1_dynamic > 0 AND #gnss_jammed > 0 THEN
    REJECT;
FI;

/* ECDIS requires GNSS for nominal route monitoring. */
IF #ecdis_nominal > 0 AND #gnss_jammed > 0 THEN
    REJECT;
FI;

/* Nav becomes degraded if GNSS is jammed. */
IF #gnss_jammed > 0 AND #nav_degraded == 0 THEN
    REJECT;
FI;

/* High draft vessels maneuvering in port require high tide. */
IF #vessel_maneuvering_port > 0 AND #tide_low > 0 THEN
    REJECT;
FI;

/* Anchor management requires the vessel to actually anchor. */
IF #vts_managing_anchorage > 0 AND #vessel_anchored == 0 THEN
    REJECT;
FI;


/* ═══════════════════════════════════════════
   COORDINATION (PRECEDES)
═══════════════════════════════════════════ */

/* GNSS → AIS: Satellite fix feeds the transponder. */
IF #precise_position_fix > 0 AND #tx_msg1_dynamic > 0 THEN
    COORDINATE $p : precise_position_fix FROM GNSS_System,
               $t : tx_msg1_dynamic      FROM Vessel_AIS
        DO ADD $p PRECEDES $t; OD;
FI;

/* AIS → VTS: Transponder data ingested by shore radar/VTS. */
IF #tx_msg1_dynamic > 0 AND #ais_ingestion > 0 THEN
    COORDINATE $t : tx_msg1_dynamic FROM Vessel_AIS,
               $i : ais_ingestion   FROM VTS_Center
        DO ADD $t PRECEDES $i; OD;
FI;

/* VTS → Vessel: VTS conflict warning received by bridge. */
IF #conflict_identified > 0 AND #Rule_16_take_early_action > 0 THEN
    COORDINATE $c : conflict_identified       FROM VTS_Center,
               $r : Rule_16_take_early_action FROM Vessel_Navigation
        DO ADD $c PRECEDES $r; OD;
FI;

/* Tugs → Vessel: Tug push/pull enables port maneuver. */
IF #pushing_pulling > 0 AND #bow_thrusters_active > 0 THEN
    COORDINATE $p : pushing_pulling      FROM Tugboat_Fleet,
               $b : bow_thrusters_active FROM Vessel_Kinematics
        DO ADD $p PRECEDES $b; OD;
FI;

/* Vessel → Port: Mooring enables cargo ops. */
IF #lines_fast > 0 AND #sts_cranes_working > 0 THEN
    COORDINATE $l : lines_fast         FROM Vessel_Kinematics,
               $c : sts_cranes_working FROM Port_Terminal
        DO ADD $l PRECEDES $c; OD;
FI;
