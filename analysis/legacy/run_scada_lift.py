import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline"))
from explore_lift import ModelConfig, ForcedPair, analyze
# usage: python run_scada_lift.py <scada_constrained_traces.db>
CONFIG = ModelConfig(
    name="scada",
    db_path=sys.argv[1],
    table="trace_states_constrained",
    components=["generation_plant","substation_relay_ied","substation_breaker",
               "scada_control_center","transmission_line","distribution_network",
               "comm_network","smart_meter_ami"],
    top_k=25,
    forced=[
        ForcedPair("ot_net_partitioned","scada_blind","REJECT: partition->blind"),
        ForcedPair("dist_feeder_fault","ami_blackout_detected","REJECT: feeder fault->blackout"),
        ForcedPair("ems_load_shedding","ami_disconnect_active","REJECT: load shed->disconnect"),
    ],
    mutex=[
        ForcedPair("ied_issuing_goose_trip","ot_net_partitioned","REJECT: no GOOSE on partition"),
        ForcedPair("microgrid_islanded","line_nominal","REJECT: island only on non-nominal line"),
    ],
)
if __name__=="__main__":
    analyze(CONFIG)
