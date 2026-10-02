import json
import math
import os
from collections import defaultdict
from itertools import product
from scipy.stats import norm

GRY_UNCONSTRAINED = "data/unconstrained.gry"
GRY_CONSTRAINED = "data/constrained.gry"
OUTPUT_FILE = "data/differential_analysis_results.txt"

COMPONENTS = [
    "Solar Inverter", "EV System", "Home Battery",
    "HEMS", "Grid Connection", "Thermal Loads", "Comm Gateway"
]

COL_NAMES = {
    "Solar Inverter":  "solar_inverter",
    "EV System":       "ev_system",
    "Home Battery":    "home_battery",
    "HEMS":            "hems",
    "Grid Connection": "grid_connection",
    "Thermal Loads":   "thermal_loads",
    "Comm Gateway":    "comm_gateway"
}

def get_precedence_pairs(nodes, edges):
    node_labels = {}
    action_ids = set()
    for n in nodes:
        node_labels[n["id"]] = n["label"]
        if n["type"] == "A":
            action_ids.add(n["id"])
            
    adj = {aid: [] for aid in action_ids}
    for e in edges:
        if e.get("relation") == "FOLLOWS":
            from_id = e["from_id"]
            to_id = e["to_id"]
            if from_id in action_ids and to_id in action_ids:
                adj[from_id].append(to_id)
                
    reachable_pairs = set()
    for start_id in action_ids:
        start_label = node_labels[start_id]
        visited = set()
        stack = [start_id]
        while stack:
            curr = stack.pop()
            if curr != start_id:
                curr_label = node_labels[curr]
                reachable_pairs.add((start_label, curr_label))
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
                    
    return reachable_pairs

def process_gry_file(path):
    print(f"Processing {path}...")
    size_mb = os.path.getsize(path) / 1e6
    print(f"  File size: {size_mb:.1f} MB")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    graphs = data.get("graphs", [])
    total_traces = 0
    
    # Statistical accumulators
    single_counts = defaultdict(int)
    cooccur_counts = defaultdict(int)
    precedence_counts = defaultdict(int)
    
    # Keep track of unique labels per component
    comp_states_set = defaultdict(set)
    action_events_set = set()
    
    for g in graphs:
        trace = g.get("trace")
        if trace is None:
            continue
        total_traces += 1
        
        nodes = trace.get("nodes", [])
        edges = trace.get("edges", [])
        
        parent_map = {}
        for edge in edges:
            if edge.get("relation") == "IN":
                parent_map[edge["to_id"]] = edge["from_id"]
                
        node_map = {n["id"]: n for n in nodes}
        
        # 1. Extract active state choices
        states = {}
        for node in nodes:
            if node["type"] == "C":
                pid = parent_map.get(node["id"])
                if pid and pid in node_map:
                    root_label = node_map[pid]["label"]
                    if root_label in COL_NAMES:
                        col = COL_NAMES[root_label]
                        states[col] = node["label"]
                        comp_states_set[col].add(node["label"])
                        
        # Record single states
        for col, state in states.items():
            single_counts[(col, state)] += 1
            
        # Record co-occurrences (cross-component)
        cols = list(states.keys())
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                col_x, col_y = cols[i], cols[j]
                sx, sy = states[col_x], states[col_y]
                # Order alphabetically by column name to ensure symmetric keys
                if col_x < col_y:
                    cooccur_counts[(col_x, sx, col_y, sy)] += 1
                else:
                    cooccur_counts[(col_y, sy, col_x, sx)] += 1
                    
        # 2. Extract precedence orderings
        for n in nodes:
            if n["type"] == "A":
                action_events_set.add(n["label"])
                
        prec_pairs = get_precedence_pairs(nodes, edges)
        for pair in prec_pairs:
            precedence_counts[pair] += 1
            
        if total_traces % 5000 == 0:
            print(f"  ... processed {total_traces} traces")
            
    print(f"  Done. Total traces parsed: {total_traces}")
    return total_traces, single_counts, cooccur_counts, precedence_counts, comp_states_set, action_events_set

def main():
    # Process unconstrained
    N1, single1, cooccur1, prec1, comp_states1, acts1 = process_gry_file(GRY_UNCONSTRAINED)
    
    # Process constrained
    N2, single2, cooccur2, prec2, comp_states2, acts2 = process_gry_file(GRY_CONSTRAINED)
    
    # Merge states and actions
    all_comp_states = defaultdict(set)
    for col in COL_NAMES.values():
        all_comp_states[col] = comp_states1[col].union(comp_states2[col])
        
    all_actions = acts1.union(acts2)
    
    results_single = []
    results_cooccur = []
    results_precedence = []
    
    # =================================================================
    # PART 1: SINGLE-STATE ANALYSIS
    # =================================================================
    single_hypotheses = []
    for col, states in all_comp_states.items():
        for s in states:
            single_hypotheses.append((col, s))
            
    alpha = 0.05
    bonf_alpha_single = alpha / len(single_hypotheses)
    bonf_z_single = norm.ppf(1 - bonf_alpha_single / 2)
    
    for col, s in single_hypotheses:
        x1 = single1.get((col, s), 0)
        x2 = single2.get((col, s), 0)
        p1, p2 = x1/N1, x2/N2
        p_pool = (x1+x2)/(N1+N2)
        z = (p2-p1) / math.sqrt(p_pool*(1-p_pool)*(1/N1 + 1/N2)) if p_pool > 0 and p_pool < 1 else 0.0
        results_single.append({
            'col': col, 'state': s, 'p1': p1, 'p2': p2, 'z': z, 'sig': abs(z) > bonf_z_single
        })
        
    # =================================================================
    # PART 2: CO-OCCURRENCE ANALYSIS
    # =================================================================
    cooccur_hypotheses = []
    cols = list(COL_NAMES.values())
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col_x, col_y = cols[i], cols[j]
            for sx in all_comp_states[col_x]:
                for sy in all_comp_states[col_y]:
                    if col_x < col_y:
                        cooccur_hypotheses.append((col_x, sx, col_y, sy))
                    else:
                        cooccur_hypotheses.append((col_y, sy, col_x, sx))
                        
    bonf_alpha_cooccur = alpha / len(cooccur_hypotheses)
    bonf_z_cooccur = norm.ppf(1 - bonf_alpha_cooccur / 2)
    
    for cx, sx, cy, sy in cooccur_hypotheses:
        key = (cx, sx, cy, sy)
        x1 = cooccur1.get(key, 0)
        x2 = cooccur2.get(key, 0)
        p1, p2 = x1/N1, x2/N2
        p_pool = (x1+x2)/(N1+N2)
        z = (p2-p1) / math.sqrt(p_pool*(1-p_pool)*(1/N1 + 1/N2)) if p_pool > 0 and p_pool < 1 else 0.0
        results_cooccur.append({
            'cx': cx, 'sx': sx, 'cy': cy, 'sy': sy, 'p1': p1, 'p2': p2, 'z': z, 'sig': abs(z) > bonf_z_cooccur
        })
        
    # =================================================================
    # PART 3: PRECEDENCE ANALYSIS
    # =================================================================
    precedence_hypotheses = []
    for act_a in all_actions:
        for act_b in all_actions:
            if act_a != act_b:
                precedence_hypotheses.append((act_a, act_b))
                
    bonf_alpha_prec = alpha / len(precedence_hypotheses)
    bonf_z_prec = norm.ppf(1 - bonf_alpha_prec / 2)
    
    for act_a, act_b in precedence_hypotheses:
        x1 = prec1.get((act_a, act_b), 0)
        x2 = prec2.get((act_a, act_b), 0)
        p1, p2 = x1/N1, x2/N2
        p_pool = (x1+x2)/(N1+N2)
        z = (p2-p1) / math.sqrt(p_pool*(1-p_pool)*(1/N1 + 1/N2)) if p_pool > 0 and p_pool < 1 else 0.0
        results_precedence.append({
            'act_a': act_a, 'act_b': act_b, 'p1': p1, 'p2': p2, 'z': z, 'sig': abs(z) > bonf_z_prec
        })
        
    # =================================================================
    # WRITE OUTPUT
    # =================================================================
    # Sort
    sig_single_supp = sorted([r for r in results_single if r['z'] < 0 and r['sig']], key=lambda r: r['z'])
    sig_single_boost = sorted([r for r in results_single if r['z'] > 0 and r['sig']], key=lambda r: r['z'], reverse=True)
    
    sig_cooccur_supp = sorted([r for r in results_cooccur if r['z'] < 0 and r['sig']], key=lambda r: r['z'])
    sig_cooccur_boost = sorted([r for r in results_cooccur if r['z'] > 0 and r['sig']], key=lambda r: r['z'], reverse=True)
    
    sig_prec_supp = sorted([r for r in results_precedence if r['z'] < 0 and r['sig']], key=lambda r: r['z'])
    sig_prec_boost = sorted([r for r in results_precedence if r['z'] > 0 and r['sig']], key=lambda r: r['z'], reverse=True)
    
    # Console output
    print(f"\n{'='*70}\nDIFFERENTIAL ANALYSIS SUMMARY\n{'='*70}")
    print(f"Unconstrained Traces (N1): {N1}")
    print(f"Constrained Traces (N2): {N2}")
    print(f"\n1. Single States:")
    print(f"   Critical z: {bonf_z_single:.2f}")
    print(f"   Suppressed: {len(sig_single_supp)} | Boosted: {len(sig_single_boost)}")
    print(f"2. Co-occurrences:")
    print(f"   Critical z: {bonf_z_cooccur:.2f}")
    print(f"   Suppressed: {len(sig_cooccur_supp)} | Boosted: {len(sig_cooccur_boost)}")
    print(f"3. Precedences:")
    print(f"   Critical z: {bonf_z_prec:.2f}")
    print(f"   Suppressed: {len(sig_prec_supp)} | Boosted: {len(sig_prec_boost)}")
    
    print("\nTOP 10 SUPPRESSED CO-OCCURRENCES (Mutual Exclusions):")
    for r in sig_cooccur_supp[:10]:
        print(f"  {r['sx']:<28} + {r['sy']:<28}  p1={r['p1']:>5.1%} p2={r['p2']:>5.1%} z={r['z']:>7.2f}")
        
    print("\nTOP 10 BOOSTED PRECEDENCES (Emergent Synchronizations):")
    for r in sig_prec_boost[:10]:
        print(f"  {r['act_a']:<28} BEFORE {r['act_b']:<28}  p1={r['p1']:>5.1%} p2={r['p2']:>5.1%} z={r['z']:>7.2f}")
        
    with open(OUTPUT_FILE, 'w') as f:
        f.write("=" * 120 + "\n")
        f.write("UNIFIED DIFFERENTIAL ANALYSIS — SMART HOME MODEL\n")
        f.write(f"Unconstrained Traces: {N1}\n")
        f.write(f"Constrained Traces:   {N2}\n")
        f.write("=" * 120 + "\n\n")
        
        # 1. Single States
        f.write(f"1. SINGLE STATE DEVIATIONS (Critical z = {bonf_z_single:.2f})\n")
        f.write("-" * 120 + "\n")
        f.write("SUPPRESSED STATES:\n")
        for r in sig_single_supp:
            f.write(f"  {r['col']:<20} {r['state']:<32}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
        f.write("\nBOOSTED STATES:\n")
        for r in sig_single_boost:
            f.write(f"  {r['col']:<20} {r['state']:<32}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
            
        # 2. Co-occurrences
        f.write(f"\n\n2. CO-OCCURRENCE DEVIATIONS (Critical z = {bonf_z_cooccur:.2f})\n")
        f.write("-" * 120 + "\n")
        f.write("SUPPRESSED CO-OCCURRENCES:\n")
        for r in sig_cooccur_supp:
            f.write(f"  {r['sx']:<30} + {r['sy']:<30}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
        f.write("\nBOOSTED CO-OCCURRENCES:\n")
        for r in sig_cooccur_boost:
            f.write(f"  {r['sx']:<30} + {r['sy']:<30}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
            
        # 3. Precedence
        f.write(f"\n\n3. PRECEDENCE DEVIATIONS (Critical z = {bonf_z_prec:.2f})\n")
        f.write("-" * 120 + "\n")
        f.write("SUPPRESSED EVENT ORDERINGS:\n")
        for r in sig_prec_supp:
            f.write(f"  {r['act_a']:<35} BEFORE {r['act_b']:<35}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
        f.write("\nBOOSTED EVENT ORDERINGS:\n")
        for r in sig_prec_boost:
            f.write(f"  {r['act_a']:<35} BEFORE {r['act_b']:<35}  p1={r['p1']:>6.2%} p2={r['p2']:>6.2%} z={r['z']:>8.2f}\n")
            
    print(f"\nFull detailed results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
