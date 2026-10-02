## INSuRE+C Schema Scanner

Schema:  Smart_Home_Energy_Composed.mp
Traces:  constrained.gry
States:  30  Orderings: 3  REJECTs: 14

Total candidate findings: 8
  Shape A: 1
  Shape B: 5
  Shape C: 2

### Shape A -- vacuous-foreach gaps

A1. Ordering 'commanding_export BEFORE delivering_energy' is vacuously satisfiable when battery_discharging is active but grid_services_mode is absent. No REJECT enforces battery_discharging -> (grid_services_mode).
    Suggested REJECT:
        IF #battery_discharging > 0 AND #grid_services_mode == 0 THEN REJECT; FI;
    Trace evidence: 4720 of 18080 traces violate this proposed rule (26.1%)
        trace #225: Comm_Gateway=gateway_online, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #226: Comm_Gateway=gateway_online, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #227: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full

### Shape B -- symmetric REJECT completion

B1. Schema has rule 'battery_charging requires (importing_power | solar_curtailed | solar_producing)'. vehicle_charging (shared-token analog, active state) has no analogous rule.
    Suggested REJECT:
        IF #vehicle_charging > 0 AND #importing_power == 0 AND #solar_curtailed == 0 AND #solar_producing == 0 THEN REJECT; FI;
    Trace evidence: 924 of 18080 traces violate this proposed rule (5.1%)
        trace #11973: Comm_Gateway=gateway_online, EV_System=vehicle_charging, Grid_Connection=exporting_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_sleeping, Thermal_Loads=loads_running_full
        trace #11974: Comm_Gateway=gateway_online, EV_System=vehicle_charging, Grid_Connection=exporting_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_sleeping, Thermal_Loads=loads_running_full
        trace #11975: Comm_Gateway=gateway_offline, EV_System=vehicle_charging, Grid_Connection=exporting_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_sleeping, Thermal_Loads=loads_running_full

B2. Schema has rule 'grid_services_mode requires (gateway_online)'. backup_reserve_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #backup_reserve_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;
    Trace evidence: 1488 of 18080 traces violate this proposed rule (8.2%)
        trace #87: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=backup_reserve_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #88: Comm_Gateway=gateway_updating, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=backup_reserve_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #91: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=backup_reserve_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_reduced

B3. Schema has rule 'grid_services_mode requires (gateway_online)'. manual_override_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #manual_override_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;
    Trace evidence: 2236 of 18080 traces violate this proposed rule (12.4%)
        trace #177: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=manual_override_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #178: Comm_Gateway=gateway_updating, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=manual_override_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #181: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=manual_override_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_reduced

B4. Schema has rule 'grid_services_mode requires (gateway_online)'. self_consumption_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #self_consumption_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;
    Trace evidence: 1488 of 18080 traces violate this proposed rule (8.2%)
        trace #3: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #4: Comm_Gateway=gateway_updating, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #7: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_reduced

B5. Schema has rule 'grid_services_mode requires (gateway_online)'. time_of_use_mode (same-root sibling, active state) has no analogous rule.
    Suggested REJECT:
        IF #time_of_use_mode > 0 AND #gateway_online == 0 THEN REJECT; FI;
    Trace evidence: 1488 of 18080 traces violate this proposed rule (8.2%)
        trace #45: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=time_of_use_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #46: Comm_Gateway=gateway_updating, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=time_of_use_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #49: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=time_of_use_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_reduced

### Shape C -- optional-event escalation

C1. REJECT triggered by optional event 'sending_to_grid' of state 'battery_discharging'. When 'sending_to_grid' does not fire, 'battery_discharging' can be active without requiring (exporting_power). Escalating to parent state closes this gap.
    Suggested REJECT:
        IF #battery_discharging > 0 AND #exporting_power == 0 THEN REJECT; FI;
    Trace evidence: 3000 of 18080 traces violate this proposed rule (16.6%)
        trace #225: Comm_Gateway=gateway_online, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #226: Comm_Gateway=gateway_online, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #227: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=importing_power, HEMS=self_consumption_mode, Home_Battery=battery_discharging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full

C2. REJECT triggered by optional event 'curtailment_applied' of state 'demand_response_event'. When 'curtailment_applied' does not fire, 'demand_response_event' can be active without requiring (gateway_online). Escalating to parent state closes this gap.
    Suggested REJECT:
        IF #demand_response_event > 0 AND #gateway_online == 0 THEN REJECT; FI;
    Trace evidence: 1800 of 18080 traces violate this proposed rule (10.0%)
        trace #27: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=demand_response_event, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #28: Comm_Gateway=gateway_updating, EV_System=no_vehicle_present, Grid_Connection=demand_response_event, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_full
        trace #31: Comm_Gateway=gateway_offline, EV_System=no_vehicle_present, Grid_Connection=demand_response_event, HEMS=self_consumption_mode, Home_Battery=battery_charging, Solar_Inverter=solar_producing, Thermal_Loads=loads_running_reduced
