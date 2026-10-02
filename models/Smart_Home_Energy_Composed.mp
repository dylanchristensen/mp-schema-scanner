/* ═══════════════════════════════════════════════════════════════
   Smart Home Energy Ecosystem — SoS Model
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Composed 7-ROOT model of a residential energy ecosystem.
   ENSURE FOREACH for ordering constraints,
   REJECT for presence and mutual-exclusion constraints.

   Components:
     - Solar_Inverter   -- PV generation (SunSpec Modbus)
     - EV_System        -- EVSE + vehicle BMS (SAE J1772, OCPP 1.6)
     - Home_Battery     -- Stationary storage (Tesla Powerwall, Enphase, LG)
     - HEMS             -- Policy/control layer (Tesla Energy, Span, Savant)
     - Grid_Connection  -- Utility interconnection (Landis+Gyr, IEEE 2030.5)
     - Thermal_Loads    -- HVAC + water heater (Nest, Ecobee, Wiser)
     - Comm_Gateway     -- Communication hub (Enphase IQ Gateway, Tesla GW)
═══════════════════════════════════════════════════════════════ */

SCHEMA Smart_Home_Energy_Composed

ROOT Solar_Inverter :
    ( solar_producing | solar_curtailed | solar_sleeping | solar_faulted );

ROOT EV_System :
    ( no_vehicle_present | vehicle_plugged_idle | vehicle_charging
    | charge_suspended   | charger_faulted );

ROOT Home_Battery :
    ( battery_charging | battery_discharging | battery_standby
    | battery_depleted | battery_islanded );

ROOT HEMS :
    ( self_consumption_mode | time_of_use_mode | backup_reserve_mode
    | grid_services_mode    | manual_override_mode );

ROOT Grid_Connection :
    ( importing_power | exporting_power
    | grid_outage     | demand_response_event );

ROOT Thermal_Loads :
    ( loads_running_full | loads_running_reduced
    | loads_idle         | loads_shed_for_dr );

ROOT Comm_Gateway :
    ( gateway_online | gateway_offline | gateway_updating );


/* ═══════════════════════════════════════════
   COMPONENT BEHAVIORS
═══════════════════════════════════════════ */

/* --- Solar Inverter --- */
solar_producing :
    solar_power_available;

solar_curtailed :
    limited_solar_available;

solar_sleeping : ;

solar_faulted :
    inverter_error;

/* --- EV System --- */
no_vehicle_present : ;

vehicle_plugged_idle :
    pilot_signal_active;

vehicle_charging :
    charge_requested
    charger_delivering
    vehicle_drawing;

charge_suspended :
    charge_paused;

charger_faulted :
    charger_error;

/* --- Home Battery --- */
battery_charging :
    absorbing_energy;

battery_discharging :
    delivering_energy
    [sending_to_grid];

battery_standby : ;

battery_depleted : ;

battery_islanded :
    powering_home_offgrid;

/* --- HEMS --- */
self_consumption_mode :
    maximizing_solar_use;

time_of_use_mode :
    shifting_to_offpeak;

backup_reserve_mode :
    holding_reserve;

grid_services_mode :
    enrolled_in_vpp
    [commanding_export];

manual_override_mode :
    owner_in_control;

/* --- Grid Connection --- */
importing_power :
    drawing_from_grid;

exporting_power :
    sending_to_utility;

grid_outage :
    grid_unavailable;

demand_response_event :
    dr_signal_received
    [curtailment_applied];

/* --- Thermal Loads --- */
loads_running_full :
    full_thermal_consumption;

loads_running_reduced :
    reduced_thermal_consumption;

loads_idle : ;

loads_shed_for_dr :
    shedding_loads;

/* --- Comm Gateway --- */
gateway_online :
    coordinating_devices
    [cloud_connected];

gateway_offline : ;

gateway_updating :
    installing_update;


/* ═══════════════════════════════════════════
   ORDERING CONSTRAINTS (ENSURE FOREACH)
   Transitive temporal ordering between events.
   These filter traces where ordering is violated.
═══════════════════════════════════════════ */

/* HEMS → Home Battery: export command precedes energy delivery */
ENSURE FOREACH $h: commanding_export, $b: delivering_energy
    ($h BEFORE $b);

/* Grid Connection: DR signal precedes curtailment within the event */
ENSURE FOREACH $d: dr_signal_received, $c: curtailment_applied
    ($d BEFORE $c);

/* Grid → Thermal Loads: DR signal precedes load shedding */
ENSURE FOREACH $d: dr_signal_received, $l: shedding_loads
    ($d BEFORE $l);


/* ═══════════════════════════════════════════
   PRESENCE CONSTRAINTS (REJECT)
   Hard physical/logical constraints.
   These eliminate impossible traces entirely.
═══════════════════════════════════════════ */

/* --- Energy flow: every active consumer or exporter needs a source --- */

/* Battery can only charge from an available energy source */
IF #battery_charging > 0
    AND #solar_producing == 0
    AND #solar_curtailed == 0
    AND #importing_power == 0 THEN
    REJECT;
FI;

/* Grid export must be sourced from solar or battery */
IF #exporting_power > 0
    AND #solar_producing == 0
    AND #solar_curtailed == 0
    AND #battery_discharging == 0 THEN
    REJECT;
FI;

/* Battery sending to grid requires the grid to be in exporting state */
IF #sending_to_grid > 0 AND #exporting_power == 0 THEN
    REJECT;
FI;

/* Battery can only island during an outage or owner override */
IF #battery_islanded > 0
    AND #grid_outage == 0
    AND #manual_override_mode == 0 THEN
    REJECT;
FI;

/* Loads can only be shed for DR participation or owner override */
IF #loads_shed_for_dr > 0
    AND #demand_response_event == 0
    AND #manual_override_mode == 0 THEN
    REJECT;
FI;


/* --- Communication dependencies ---
   Utility-facing actions (grid services, curtailment) require an
   online communication gateway. */

/* Grid-services participation requires online communication */
IF #grid_services_mode > 0 AND #gateway_online == 0 THEN
    REJECT;
FI;

/* Curtailment requires online communication to receive utility signals */
IF #curtailment_applied > 0 AND #gateway_online == 0 THEN
    REJECT;
FI;

/* Grid-services participation is incompatible with a grid outage */
IF #grid_services_mode > 0 AND #grid_outage > 0 THEN
    REJECT;
FI;


/* --- Grid-outage operating envelope ---
   During a grid outage the home is energy-isolated. Energy-generating
   or consuming activities are only legal when the battery is in
   islanded mode powering the home off-grid. Battery charging is
   forbidden during outage regardless of islanded state. */

/* Battery cannot charge during a grid outage */
IF #battery_charging > 0 AND #grid_outage > 0 THEN
    REJECT;
FI;

/* Solar production during outage requires islanded battery */
IF #solar_producing > 0
    AND #grid_outage > 0
    AND #battery_islanded == 0 THEN
    REJECT;
FI;

IF #solar_curtailed > 0
    AND #grid_outage > 0
    AND #battery_islanded == 0 THEN
    REJECT;
FI;

/* EV charging during outage requires islanded battery */
IF #vehicle_charging > 0
    AND #grid_outage > 0
    AND #battery_islanded == 0 THEN
    REJECT;
FI;

/* Thermal loads during outage require islanded battery */
IF #loads_running_full > 0
    AND #grid_outage > 0
    AND #battery_islanded == 0 THEN
    REJECT;
FI;

IF #loads_running_reduced > 0
    AND #grid_outage > 0
    AND #battery_islanded == 0 THEN
    REJECT;
FI;
