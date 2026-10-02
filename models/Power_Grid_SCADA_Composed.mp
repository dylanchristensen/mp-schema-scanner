/* ═══════════════════════════════════════════════════════════════
   Modern Power Grid & Wide-Area SCADA — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Composed 8-ROOT model of a Transmission/Distribution Grid.
   Grounded in real industrial control protocols.

   Sources:
     - IEC 61850: Substation Automation Standard (GOOSE, MMS)
     - DNP3: IEEE 1815 SCADA Telemetry Protocol
     - NERC CIP: Critical Infrastructure Protection
     - IEEE C37.94: Teleprotection standards

   Components:
     - Generation_Plant     -- Baseload/peaking power source
     - Substation_Relay_IED -- Intelligent Electronic Device (Brain)
     - Substation_Breaker   -- High voltage circuit breaker (Muscle)
     - SCADA_Control_Center -- Energy Management System (EMS)
     - Transmission_Line    -- High voltage transit corridor
     - Distribution_Network -- Local grid feeders
     - Comm_Network         -- Fiber/Microwave OT network
     - Smart_Meter_AMI      -- Advanced Metering Infrastructure
═══════════════════════════════════════════════════════════════ */

SCHEMA Power_Grid_SCADA_Composed

/* ═══════════════════════════════════════════
   ROOT COMPONENTS
═══════════════════════════════════════════ */

ROOT Generation_Plant :
    ( baseload_running | peaking_plant_active
    | ramping_up | tripped_offline );

ROOT Substation_Relay_IED :
    ( ied_monitoring | ied_overcurrent_detected
    | ied_issuing_goose_trip | ied_locked_out );

ROOT Substation_Breaker :
    ( breaker_closed | breaker_open
    | breaker_opening | breaker_failure_to_trip );

ROOT SCADA_Control_Center :
    ( ems_nominal | ems_agc_active
    | ems_load_shedding | scada_blind );

ROOT Transmission_Line :
    ( line_nominal | line_overloaded
    | line_faulted | line_de_energized );

ROOT Distribution_Network :
    ( dist_nominal | dist_peak_load
    | dist_feeder_fault | microgrid_islanded );

ROOT Comm_Network :
    ( ot_net_nominal | ot_net_congested
    | ot_net_partitioned );

ROOT Smart_Meter_AMI :
    ( ami_reporting | ami_demand_response
    | ami_disconnect_active | ami_blackout_detected );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
═══════════════════════════════════════════ */

/* --- Generation Plant --- */
baseload_running :
    spinning_reserve_active
    synced_to_grid;

peaking_plant_active :
    rapid_response_online
    synced_to_grid;

ramping_up :
    turbine_spin_up;

tripped_offline :
    generator_protection_trip
    frequency_dropping;

/* --- Substation Relay IED ---
   IEC 61850 logic. */
ied_monitoring :
    sampling_ct_vt
    mms_reporting_to_scada;

ied_overcurrent_detected :
    protection_pickup
    mms_reporting_to_scada;

ied_issuing_goose_trip :
    publishing_goose_message
    event_logged;

ied_locked_out :
    requires_manual_reset;

/* --- Substation Breaker --- */
breaker_closed :
    contacts_closed
    carrying_current;

breaker_open :
    contacts_open
    arc_extinguished;

breaker_opening :
    trip_coil_energized
    arcing;

breaker_failure_to_trip :
    mechanism_stuck
    breaker_failure_initiate;  /* Triggers backup relays */

/* --- SCADA Control Center --- */
ems_nominal :
    state_estimation_converged
    dnp3_polling_active;

ems_agc_active :
    automatic_generation_control
    dnp3_polling_active;

ems_load_shedding :
    underfrequency_detected
    issuing_trip_commands;

scada_blind :
    loss_of_telemetry
    alarms_suppressed;

/* --- Transmission Line --- */
line_nominal :
    voltage_within_limits
    thermal_limits_ok;

line_overloaded :
    sagging_conductors
    thermal_limit_exceeded;

line_faulted :
    phase_to_ground_fault
    high_fault_current;

line_de_energized :
    zero_voltage;

/* --- Distribution Network --- */
dist_nominal :
    feeders_energized;

dist_peak_load :
    voltage_drop_detected;

dist_feeder_fault :
    tree_on_line;

microgrid_islanded :
    disconnected_from_transmission
    local_generation_active;

/* --- Comm Network --- */
ot_net_nominal :
    goose_multicast_flowing
    dnp3_tcp_flowing;

ot_net_congested :
    packet_loss_detected
    latency_spikes;

ot_net_partitioned :
    link_down
    substation_isolated;

/* --- Smart Meter AMI --- */
ami_reporting :
    mesh_network_active
    sending_kwh_data;

ami_demand_response :
    hvac_curtailed_by_utility;

ami_disconnect_active :
    remote_switch_open;

ami_blackout_detected :
    last_gasp_message_sent;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
═══════════════════════════════════════════ */

/* IEC 61850: IED must detect overcurrent before publishing GOOSE trip. */
ENSURE FOREACH $o: protection_pickup, $g: publishing_goose_message
    ($o BEFORE $g);

/* Breaker trip coil must be energized before contacts fully open. */
ENSURE FOREACH $t: trip_coil_energized, $c: contacts_open
    ($t BEFORE $c);

/* SCADA must detect underfrequency before issuing load shed trips. */
ENSURE FOREACH $u: underfrequency_detected, $i: issuing_trip_commands
    ($u BEFORE $i);

/* Line must fault before breaker trip coil is energized by relay. */
ENSURE FOREACH $f: high_fault_current, $t: trip_coil_energized
    ($f BEFORE $t);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
═══════════════════════════════════════════ */

/* IEC 61850 GOOSE multicast relies on the OT network.
   Cannot issue GOOSE trip if network is partitioned. */
IF #ied_issuing_goose_trip > 0 AND #ot_net_partitioned > 0 THEN
    REJECT;
FI;

/* SCADA is blind if the OT network is partitioned. */
IF #ot_net_partitioned > 0 AND #scada_blind == 0 THEN
    REJECT;
FI;

/* Breaker opening state is required to transition to open state.
   (Logical representation that the physical act must occur). */
IF #breaker_open > 0 AND #breaker_opening == 0 THEN
    REJECT;
FI;

/* Transmission line cannot be nominal if it's faulted. */
IF #line_faulted > 0 AND #line_nominal > 0 THEN
    REJECT;
FI;

/* If the line is faulted and the breaker fails to trip, 
   the fault remains on the system. */
IF #line_faulted > 0 AND #breaker_failure_to_trip > 0 AND #line_de_energized > 0 THEN
    REJECT; /* Cannot de-energize if the breaker is stuck closed */
FI;

/* Plant trips offline if a fault is uncleared (breaker failure). */
IF #line_faulted > 0 AND #breaker_failure_to_trip > 0 AND #baseload_running > 0 THEN
    REJECT;
FI;

/* Microgrid islanding happens during transmission outages. */
IF #microgrid_islanded > 0 AND #line_nominal > 0 THEN
    REJECT;
FI;

/* AMI detects blackout if distribution feeder faults. */
IF #dist_feeder_fault > 0 AND #ami_blackout_detected == 0 THEN
    REJECT;
FI;

/* Load shedding requires AMI disconnects or feeder trips. */
IF #ems_load_shedding > 0 AND #ami_disconnect_active == 0 THEN
    REJECT;
FI;


/* ═══════════════════════════════════════════
   COORDINATION (PRECEDES)
═══════════════════════════════════════════ */

/* Physics → Cyber: Line fault causes relay pickup. */
IF #high_fault_current > 0 AND #protection_pickup > 0 THEN
    COORDINATE $f : high_fault_current FROM Transmission_Line,
               $p : protection_pickup  FROM Substation_Relay_IED
        DO ADD $f PRECEDES $p; OD;
FI;

/* Cyber → Physics: GOOSE message causes breaker trip coil to energize. */
IF #publishing_goose_message > 0 AND #trip_coil_energized > 0 THEN
    COORDINATE $g : publishing_goose_message FROM Substation_Relay_IED,
               $t : trip_coil_energized      FROM Substation_Breaker
        DO ADD $g PRECEDES $t; OD;
FI;

/* SCADA → Edge: Load shed command triggers AMI disconnect. */
IF #issuing_trip_commands > 0 AND #remote_switch_open > 0 THEN
    COORDINATE $i : issuing_trip_commands FROM SCADA_Control_Center,
               $r : remote_switch_open    FROM Smart_Meter_AMI
        DO ADD $i PRECEDES $r; OD;
FI;

/* Physics → SCADA: Frequency drop triggers EMS load shedding logic. */
IF #frequency_dropping > 0 AND #underfrequency_detected > 0 THEN
    COORDINATE $f : frequency_dropping      FROM Generation_Plant,
               $u : underfrequency_detected FROM SCADA_Control_Center
        DO ADD $f PRECEDES $u; OD;
FI;
