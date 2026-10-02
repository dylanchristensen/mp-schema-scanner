/* ═══════════════════════════════════════════════════════════════
   Connected Autonomous Vehicle (V2X) — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Composed 8-ROOT model of a Smart Street / V2X Ecosystem.
   Grounded in real automotive and intelligent transport protocols.

   Sources:
     - SAE J2735: DSRC Message Set Dictionary (BSM, SPaT, MAP, TIM, PSM)
     - NTCIP 1202: Actuated Signal Controller Interface Protocol (Phases, Preemption)
     - 3GPP Rel-14/15: C-V2X (PC5 direct communication, Uu network)
     - ETSI TS 102 894: Cooperative Awareness (CAM/DENM equivalents)
     - SAE J3016: Levels of Driving Automation (Level 4/5 pipeline)
     - IEEE 1609 (WAVE) / 802.11p: DSRC physical/MAC layers

   Components (map to real Smart City/AV elements):
     - AV_Kinematics    -- Physical motion of the Autonomous Vehicle
     - AV_Compute       -- Perception/Planning sensor fusion pipeline
     - AV_V2X_OBU       -- On-Board Unit for V2V/V2I communications
     - Traffic_Signal   -- Physical intersection lights (Phases)
     - Traffic_Controller-- NTCIP edge device managing signal timing
     - MEC_Server       -- Multi-access Edge Compute (Intersection manager)
     - Vulnerable_User  -- Pedestrian with V2X User Equipment (Smart device)
     - Emergency_Vehicle-- Fire/EMS unit requesting signal preemption
═══════════════════════════════════════════════════════════════ */

SCHEMA Connected_Street_V2X_Composed

/* ═══════════════════════════════════════════
   ROOT COMPONENTS
═══════════════════════════════════════════ */

ROOT AV_Kinematics :
    ( av_cruising | av_accelerating | av_braking_normal
    | av_braking_emergency | av_stopped );

ROOT AV_Compute :
    ( perception_clear | object_detected 
    | collision_predicted | sensor_degraded );

ROOT AV_V2X_OBU :
    ( obu_tx_rx_active | obu_cooperative_perception
    | obu_rx_only      | obu_isolated );

ROOT Traffic_Signal :
    ( phase_green | phase_yellow | phase_red | overlap_active );

ROOT Traffic_Controller :
    ( tc_coord_normal | tc_transit_priority
    | tc_preempt_active | tc_flash_fault );

ROOT MEC_Server :
    ( mec_monitoring_normal | mec_hazard_broadcasting
    | mec_platoon_coordinating | mec_offline );

ROOT Vulnerable_User :
    ( vru_safe_distance | vru_crossing_active
    | vru_in_roadway    | vru_device_offline );

ROOT Emergency_Vehicle :
    ( ev_inactive | ev_responding | ev_on_scene );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
═══════════════════════════════════════════ */

/* --- AV_Kinematics ---
   Real physical states of a vehicle under control. */
av_cruising :
    maintaining_speed
    lane_centering;

av_accelerating :
    throttle_applied
    speed_increasing;

av_braking_normal :
    service_brakes_applied
    speed_decreasing;

av_braking_emergency :
    aeb_activated
    abs_engaged
    max_deceleration;

av_stopped :
    zero_velocity
    auto_hold_active;

/* --- AV_Compute ---
   Real automated driving system (ADS) pipeline. */
perception_clear :
    lidar_point_cloud_fused
    camera_inference_nominal
    trajectory_planned;

object_detected :
    lidar_point_cloud_fused
    obstacle_classified
    trajectory_adjusted;

collision_predicted :
    ttc_below_threshold   /* Time-To-Collision */
    evasive_trajectory_planned;

sensor_degraded :
    sensor_blindness_detected
    fallback_mode_engaged;

/* --- AV_V2X_OBU ---
   SAE J2735 message transmission/reception. */
obu_tx_rx_active :
    tx_bsm_10hz           /* Basic Safety Message */
    rx_spat               /* Signal Phase and Timing */
    rx_map;               /* Intersection Geometry */

obu_cooperative_perception :
    tx_bsm_10hz
    rx_spat
    rx_map
    rx_sensor_sharing;    /* Exchanging raw perception data */

obu_rx_only :
    rx_spat
    rx_map
    tx_suppressed;

obu_isolated :
    no_v2x_signal;

/* --- Traffic_Signal ---
   Physical light states governed by NTCIP 1202 phases. */
phase_green :
    green_indication
    right_of_way_granted;

phase_yellow :
    yellow_indication
    clearance_interval;

phase_red :
    red_indication
    stop_bar_enforced;

overlap_active :
    green_indication
    protected_turn_active;

/* --- Traffic_Controller ---
   NTCIP 1202 logical states and commands. */
tc_coord_normal :
    running_local_pattern
    ped_recall_active;

tc_transit_priority :
    tsp_request_received
    phase_green_extended;

tc_preempt_active :
    preempt_call_received
    active_phase_terminated
    dwell_state_active;

tc_flash_fault :
    cabinet_flash_mode
    mmt_fault_detected;   /* Malfunction Management Unit */

/* --- MEC_Server ---
   Multi-access Edge Computing (Intersection Manager). */
mec_monitoring_normal :
    ingesting_bsms
    publishing_tim;       /* Traveler Information Message */

mec_hazard_broadcasting :
    ingesting_bsms
    hazard_detected
    publishing_denm;      /* Decentralized Environmental Notification */

mec_platoon_coordinating :
    ingesting_bsms
    assigning_platoon_gaps
    publishing_tim;

mec_offline :
    edge_compute_down;

/* --- Vulnerable_User ---
   SAE J2735 Personal Safety Message (PSM). */
vru_safe_distance :
    tx_psm_1hz
    on_sidewalk;

vru_crossing_active :
    tx_psm_1hz
    in_crosswalk;

vru_in_roadway :
    tx_psm_1hz
    jaywalking_detected;

vru_device_offline :
    no_psm_transmitted;

/* --- Emergency_Vehicle ---
   SAE J2735 Signal Request Message (SRM) generator. */
ev_inactive :
    ev_normal_patrol;

ev_responding :
    lights_sirens_active
    tx_high_priority_bsm
    tx_srm_preempt;       /* Signal Request Message */

ev_on_scene :
    parked_in_roadway
    tx_tim_incident;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
   Based on physical reality and V2X protocols.
═══════════════════════════════════════════ */

/* Perception pipeline: object must be classified before trajectory adjusts. */
ENSURE FOREACH $o: obstacle_classified, $t: trajectory_adjusted
    ($o BEFORE $t);

/* Time-To-Collision threshold must be breached before AEB activates. */
ENSURE FOREACH $t: ttc_below_threshold, $a: aeb_activated
    ($t BEFORE $a);

/* NTCIP 1202: Preempt call must be received before phase terminates. */
ENSURE FOREACH $p: preempt_call_received, $a: active_phase_terminated
    ($p BEFORE $a);

/* NTCIP 1202: Active phase terminates before entering preemption dwell state. */
ENSURE FOREACH $a: active_phase_terminated, $d: dwell_state_active
    ($a BEFORE $d);

/* V2X: EV must broadcast high priority BSM before MEC detects hazard. */
ENSURE FOREACH $h: tx_high_priority_bsm, $d: hazard_detected
    ($h BEFORE $d);

/* V2X: MEC detects hazard before publishing DENM/TIM. */
ENSURE FOREACH $h: hazard_detected, $p: publishing_denm
    ($h BEFORE $p);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
   Logical, physical, and regulatory invariants.
═══════════════════════════════════════════ */

/* ------- AV Physics & Perception ------- */

/* Emergency braking (AEB) requires a collision prediction. */
IF #av_braking_emergency > 0 AND #collision_predicted == 0 THEN
    REJECT;
FI;

/* AV cannot cruise if a collision is predicted. */
IF #av_cruising > 0 AND #collision_predicted > 0 THEN
    REJECT;
FI;

/* AV cannot cruise if sensors are degraded. */
IF #av_cruising > 0 AND #sensor_degraded > 0 THEN
    REJECT;
FI;

/* Trajectory adjustment requires an object detection or collision prediction. */
IF #trajectory_adjusted > 0
    AND #object_detected == 0
    AND #collision_predicted == 0 THEN
    REJECT;
FI;

/* ------- Traffic Controller Logic ------- */

/* NTCIP 1202: Normal coordination cannot occur during preemption. */
IF #tc_coord_normal > 0 AND #tc_preempt_active > 0 THEN
    REJECT;
FI;

/* Traffic signal cannot be green if controller is in flash fault mode. */
IF #phase_green > 0 AND #tc_flash_fault > 0 THEN
    REJECT;
FI;

/* NTCIP 1202: Preemption active requires an emergency vehicle request. */
IF #tc_preempt_active > 0 AND #ev_responding == 0 THEN
    REJECT;
FI;

/* ------- V2X Network Dependencies ------- */

/* Cooperative perception requires the OBU to be active and not isolated. */
IF #obu_cooperative_perception > 0
    AND #obu_isolated > 0 THEN
    REJECT;
FI;

/* MEC hazard broadcast requires at least one hazard source
   (EV responding, VRU in roadway, or AV collision predicted). */
IF #mec_hazard_broadcasting > 0
    AND #ev_responding == 0
    AND #vru_in_roadway == 0
    AND #collision_predicted == 0 THEN
    REJECT;
FI;

/* AV cannot receive SPaT/MAP if OBU is isolated. */
IF #rx_spat > 0 AND #obu_isolated > 0 THEN
    REJECT;
FI;

/* ------- System Interactions ------- */

/* AV cruising through a red light is a violation of traffic laws (unless EV).
   Assuming AV obeys laws based on SPaT. */
IF #av_cruising > 0
    AND #phase_red > 0
    AND #rx_spat > 0 THEN
    REJECT;
FI;

/* AV cannot accelerate if a VRU is in the roadway ahead, assuming V2X works. */
IF #av_accelerating > 0
    AND #vru_in_roadway > 0
    AND #obu_isolated == 0
    AND #vru_device_offline == 0 THEN
    REJECT;
FI;


/* ═══════════════════════════════════════════
   COORDINATION (PRECEDES)
   Data exchange between cyber-physical entities.
═══════════════════════════════════════════ */

/* Traffic Controller → OBU: Controller broadcasts SPaT to vehicle. */
IF #running_local_pattern > 0 AND #rx_spat > 0 THEN
    COORDINATE $t : running_local_pattern FROM Traffic_Controller,
               $r : rx_spat               FROM AV_V2X_OBU
        DO ADD $t PRECEDES $r; OD;
FI;

/* EV → Traffic Controller: EV broadcasts SRM for preemption. */
IF #tx_srm_preempt > 0 AND #preempt_call_received > 0 THEN
    COORDINATE $s : tx_srm_preempt        FROM Emergency_Vehicle,
               $p : preempt_call_received FROM Traffic_Controller
        DO ADD $s PRECEDES $p; OD;
FI;

/* VRU → MEC Server: Pedestrian PSM is ingested by Edge Server. */
IF #tx_psm_1hz > 0 AND #ingesting_bsms > 0 THEN
    COORDINATE $p : tx_psm_1hz     FROM Vulnerable_User,
               $i : ingesting_bsms FROM MEC_Server
        DO ADD $p PRECEDES $i; OD;
FI;

/* MEC Server → OBU: Edge broadcasts DENM hazard to vehicle. */
IF #publishing_denm > 0 AND #rx_sensor_sharing > 0 THEN
    COORDINATE $d : publishing_denm   FROM MEC_Server,
               $r : rx_sensor_sharing FROM AV_V2X_OBU
        DO ADD $d PRECEDES $r; OD;
FI;

/* AV Compute → AV Kinematics: Perception triggers AEB actuation. */
IF #evasive_trajectory_planned > 0 AND #aeb_activated > 0 THEN
    COORDINATE $e : evasive_trajectory_planned FROM AV_Compute,
               $a : aeb_activated              FROM AV_Kinematics
        DO ADD $e PRECEDES $a; OD;
FI;
