"""Write the composed MP file with CRLF line endings - trimmed ENSURE FOREACH."""
content = r"""/* =================================================================
   Smart_Home_Energy_Composed.mp
   NSA INSuRE+C | Summer 2026
   Dylan Christensen, Victor Sanchez, Srikar Kaligotla

   Smart Home Energy Ecosystem -- COMPOSED MODEL
   Following healthcare delivery model pattern:
     - ENSURE FOREACH ... BEFORE for ordering constraints
     - IF...THEN REJECT for presence constraints

   COMPONENTS (7 ROOTs):
     01   Solar_Inverter   -- PV generation (SunSpec Modbus)
     02   EV_System        -- Combined EVSE + vehicle BMS (SAE J1772, OCPP 1.6)
     03   Home_Battery     -- Stationary storage (Tesla Powerwall, Enphase, LG)
     04   HEMS             -- Policy/control layer (Tesla Energy, Span, Savant)
     05   Grid_Connection  -- Utility interconnection (Landis+Gyr, IEEE 2030.5)
     06   Thermal_Loads    -- Combined HVAC + water heater (Nest, Ecobee, Wiser)
     07   Comm_Gateway     -- Communication hub (Enphase IQ Gateway, Tesla GW)
   ================================================================= */

SCHEMA Smart_Home_Energy_Composed

ROOT Solar_Inverter :
    ( solar_producing | solar_curtailed | solar_sleeping | solar_faulted );

solar_producing : solar_power_available;
solar_curtailed : limited_solar_available;
solar_sleeping  : ;
solar_faulted   : inverter_error;

ROOT EV_System :
    ( no_vehicle_present | vehicle_plugged_idle | vehicle_charging
    | charge_suspended   | charger_faulted );

no_vehicle_present  : ;
vehicle_plugged_idle: pilot_signal_active;
vehicle_charging    : charge_requested charger_delivering vehicle_drawing;
charge_suspended    : charge_paused;
charger_faulted     : charger_error;

ROOT Home_Battery :
    ( battery_charging | battery_discharging | battery_standby
    | battery_depleted  | battery_islanded );

battery_charging    : absorbing_energy;
battery_discharging : delivering_energy [sending_to_grid];
battery_standby     : ;
battery_depleted    : ;
battery_islanded    : powering_home_offgrid;

ROOT HEMS :
    ( self_consumption_mode | time_of_use_mode | backup_reserve_mode
    | grid_services_mode    | manual_override_mode );

self_consumption_mode : maximizing_solar_use;
time_of_use_mode      : shifting_to_offpeak;
backup_reserve_mode   : holding_reserve;
grid_services_mode    : enrolled_in_vpp [commanding_export];
manual_override_mode  : owner_in_control;

ROOT Grid_Connection :
    ( importing_power | exporting_power
    | grid_outage     | demand_response_event );

importing_power       : drawing_from_grid;
exporting_power       : sending_to_utility;
grid_outage           : grid_unavailable;
demand_response_event : dr_signal_received [curtailment_applied];

ROOT Thermal_Loads :
    ( loads_running_full | loads_running_reduced
    | loads_idle         | loads_shed_for_dr );

loads_running_full    : full_thermal_consumption;
loads_running_reduced : reduced_thermal_consumption;
loads_idle            : ;
loads_shed_for_dr     : shedding_loads;

ROOT Comm_Gateway :
    ( gateway_online | gateway_offline | gateway_updating );

gateway_online   : coordinating_devices [cloud_connected];
gateway_offline  : ;
gateway_updating : installing_update;

/* HEMS command -> battery response */
ENSURE FOREACH $h: commanding_export, $b: delivering_energy
    ($h BEFORE $b);

/* DR signal -> curtailment applied */
ENSURE FOREACH $d: dr_signal_received, $c: curtailment_applied
    ($d BEFORE $c);

/* DR signal -> loads shed */
ENSURE FOREACH $d: dr_signal_received, $l: shedding_loads
    ($d BEFORE $l);

IF #battery_islanded > 0 AND #grid_outage == 0 AND #manual_override_mode == 0 THEN REJECT; FI;

IF #battery_charging > 0
    AND #solar_producing == 0
    AND #solar_curtailed == 0
    AND #importing_power == 0 THEN
    REJECT;
FI;

IF #exporting_power > 0
    AND #solar_producing == 0
    AND #solar_curtailed == 0
    AND #battery_discharging == 0 THEN
    REJECT;
FI;

IF #sending_to_grid > 0 AND #exporting_power == 0 THEN REJECT; FI;

IF #grid_services_mode > 0 AND #grid_outage > 0 THEN REJECT; FI;

IF #grid_services_mode > 0 AND #gateway_offline > 0 THEN REJECT; FI;
IF #grid_services_mode > 0 AND #gateway_updating > 0 THEN REJECT; FI;

IF #curtailment_applied > 0 AND #gateway_online == 0 THEN REJECT; FI;

IF #loads_shed_for_dr > 0
    AND #demand_response_event == 0
    AND #manual_override_mode == 0 THEN
    REJECT;
FI;

IF #solar_producing > 0 AND #grid_outage > 0 AND #battery_islanded == 0 THEN REJECT; FI;
IF #solar_curtailed > 0 AND #grid_outage > 0 AND #battery_islanded == 0 THEN REJECT; FI;

IF #battery_charging > 0 AND #grid_outage > 0 THEN REJECT; FI;

IF #vehicle_charging > 0 AND #grid_outage > 0 AND #battery_islanded == 0 THEN REJECT; FI;

IF #loads_running_full > 0 AND #grid_outage > 0 AND #battery_islanded == 0 THEN REJECT; FI;
IF #loads_running_reduced > 0 AND #grid_outage > 0 AND #battery_islanded == 0 THEN REJECT; FI;
"""

with open("data/Smart_Home_Energy_Composed.mp", 'w', newline='\r\n') as f:
    f.write(content.lstrip('\n'))
print('Done - 3 ENSURE FOREACH, 14 REJECTs')
