"""
Direction-A (M2) analysis on the 18,080 constrained smart-home traces.

Same procedure as the healthcare run, applied at scale. The pre-registered
candidates were sketched from reading Smart_Home_Energy_Composed.mp BEFORE
this analysis was run; they are guesses, not SME ground truth. Presence
in the top of the ranking is encouraging but not the success criterion --
the real success criterion is whether the top-K is interpretable, i.e.
whether each top-K candidate corresponds to a coherent implicit assumption
an SME could read off.

The procedure lives in explore_lift.analyze(); this file only supplies
model data.
"""

from explore_lift import (
    ModelConfig, ForcedPair, ValidationEntry, analyze,
)

# Partial-mandate REJECTs in Smart_Home_Energy_Composed.mp.
# Each "X > 0 AND no Y_i" REJECT yields partial-forced pairs (X, Y_i):
# whenever X is present, at least one Y_i must be too.
PARTIAL_FORCED = [
    ForcedPair("battery_charging", "solar_producing",
               "battery_charging requires source"),
    ForcedPair("battery_charging", "solar_curtailed",
               "battery_charging requires source"),
    ForcedPair("battery_charging", "importing_power",
               "battery_charging requires source"),
    ForcedPair("exporting_power", "solar_producing",
               "exporting_power requires source"),
    ForcedPair("exporting_power", "solar_curtailed",
               "exporting_power requires source"),
    ForcedPair("exporting_power", "battery_discharging",
               "exporting_power requires source"),
    ForcedPair("battery_islanded", "grid_outage",
               "battery_islanded requires outage/override"),
    ForcedPair("battery_islanded", "manual_override_mode",
               "battery_islanded requires outage/override"),
    ForcedPair("loads_shed_for_dr", "demand_response_event",
               "load shed requires DR event or override"),
    ForcedPair("loads_shed_for_dr", "manual_override_mode",
               "load shed requires DR event or override"),
    ForcedPair("grid_services_mode", "gateway_online",
               "grid services requires comms"),
]

# Mutex REJECTs ("X > 0 AND Y > 0" => forced absence).
MUTEX = [
    ForcedPair("grid_services_mode", "grid_outage",
               "grid services and outage are mutually exclusive"),
    ForcedPair("battery_charging", "grid_outage",
               "charging cannot happen during outage"),
]

CONFIG = ModelConfig(
    name="smart_home",
    db_path="data/smart_home_constrained_traces.db",
    table="trace_states_constrained",
    components=["solar_inverter", "ev_system", "home_battery", "hems",
                "grid_connection", "thermal_loads", "comm_gateway"],
    top_k=25,
    forced=PARTIAL_FORCED,
    mutex=MUTEX,
    validation=[
        ValidationEntry("vehicle_charging", "solar_producing",
                        "Cand 1: EV charging needs source (Shape C)"),
        ValidationEntry("vehicle_charging", "solar_curtailed",
                        "Cand 1: EV charging needs source (Shape C)"),
        ValidationEntry("vehicle_charging", "importing_power",
                        "Cand 1: EV charging needs source (Shape C)"),
        ValidationEntry("vehicle_charging", "battery_discharging",
                        "Cand 1: EV charging needs source (Shape C)"),
        ValidationEntry("loads_shed_for_dr", "gateway_online",
                        "Cand 2: load-shed needs comm (Shape C)"),
        ValidationEntry("demand_response_event", "gateway_online",
                        "Cand 3: DR signal needs comm (Shape A)"),
        ValidationEntry("self_consumption_mode", "solar_producing",
                        "Cand 4: self-consumption needs solar (Shape A)"),
        ValidationEntry("self_consumption_mode", "solar_curtailed",
                        "Cand 4: self-consumption needs solar (Shape A)"),
        ValidationEntry("self_consumption_mode", "gateway_online",
                        "Cand 5: HEMS mode needs comm (Shape B)"),
        ValidationEntry("time_of_use_mode", "gateway_online",
                        "Cand 5: HEMS mode needs comm (Shape B)"),
        ValidationEntry("backup_reserve_mode", "gateway_online",
                        "Cand 5: HEMS mode needs comm (Shape B)"),
    ],
    validation_label="PRE-REGISTERED CANDIDATES",
)


if __name__ == "__main__":
    analyze(CONFIG)
