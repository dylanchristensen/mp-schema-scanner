import sqlite3
import math
from itertools import product
from scipy.stats import norm

DB_FILE = "data/healthcare_traces.db"
COMPONENTS = ["patient", "clinical_device", "ehr_system", "physician", "pharmacy", "insurance"]

def get_db_stats(suffix):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Get total traces N
    cur.execute(f"SELECT COUNT(*) FROM traces_{suffix}")
    N = cur.fetchone()[0]
    
    # Get all unique states per component and their counts
    comp_states = {}
    state_counts = {}
    for comp in COMPONENTS:
        cur.execute(f"SELECT DISTINCT {comp} FROM trace_states_{suffix} WHERE {comp} != ''")
        comp_states[comp] = [row[0] for row in cur.fetchall()]
        for state in comp_states[comp]:
            cur.execute(f"SELECT COUNT(*) FROM trace_states_{suffix} WHERE {comp} = ?", (state,))
            state_counts[(comp, state)] = cur.fetchone()[0]
            
    # Get pairwise counts
    pair_counts = {}
    for comp_x, comp_y in product(COMPONENTS, repeat=2):
        if comp_x == comp_y:
            continue
        for state_x in comp_states[comp_x]:
            for state_y in comp_states[comp_y]:
                cur.execute(
                    f"SELECT COUNT(*) FROM trace_states_{suffix} WHERE {comp_x} = ? AND {comp_y} = ?",
                    (state_x, state_y)
                )
                pair_counts[(state_x, state_y)] = cur.fetchone()[0]
                
    conn.close()
    return N, comp_states, state_counts, pair_counts

def main():
    print("Gathering statistics from Unconstrained (healthcare Delivery scope 2)...")
    N1, states1, counts1, pairs1 = get_db_stats("unconstrained")
    print(f"  Unconstrained traces (N1): {N1}")
    
    print("\nGathering statistics from Constrained (healthcare Delivery scope 1)...")
    N2, states2, counts2, pairs2 = get_db_stats("constrained")
    print(f"  Constrained traces (N2): {N2}")
    
    # --- PART 1: SINGLE STATE (MARGINAL) DEVIATIONS ---
    print("\n" + "=" * 80)
    print("PART 1: SINGLE STATE (MARGINAL) DEVIATIONS")
    print("=" * 80)
    
    # Collect all unique states from physical baseline (unconstrained)
    all_single_states = []
    for comp in COMPONENTS:
        for state in states1[comp]:
            all_single_states.append((comp, state))
            
    total_single_hypotheses = len(all_single_states)
    alpha = 0.05
    bonf_alpha_single = alpha / total_single_hypotheses
    bonf_z_single = norm.ppf(1 - bonf_alpha_single / 2)
    print(f"Total states: {total_single_hypotheses}, Bonferroni-corrected alpha: {bonf_alpha_single:.6f}, Critical z: {bonf_z_single:.2f}")
    
    single_results = []
    for comp, state in all_single_states:
        x1 = counts1.get((comp, state), 0)
        p1 = x1 / N1
        
        x2 = counts2.get((comp, state), 0)
        p2 = x2 / N2
        
        p_pool = (x1 + x2) / (N1 + N2)
        if p_pool == 0 or p_pool == 1:
            z = 0.0
        else:
            se = math.sqrt(p_pool * (1 - p_pool) * (1/N1 + 1/N2))
            z = (p2 - p1) / se if se > 0 else 0.0
            
        single_results.append({
            'component': comp, 'state': state,
            'x1': x1, 'p1': p1,
            'x2': x2, 'p2': p2,
            'z': z,
            'sig': abs(z) > bonf_z_single
        })
        
    sig_single_suppressed = sorted([r for r in single_results if r['z'] < 0 and r['sig']], key=lambda r: r['z'])
    sig_single_boosted = sorted([r for r in single_results if r['z'] > 0 and r['sig']], key=lambda r: r['z'], reverse=True)
    
    print(f"\nSignificant single-state deviations: {len([r for r in single_results if r['sig']])} of {total_single_hypotheses}")
    print(f"  Suppressed: {len(sig_single_suppressed)}")
    print(f"  Boosted:    {len(sig_single_boosted)}")
    
    print("\nSUPPRESSED STATES (pruned or reduced in constrained model):")
    print("-" * 110)
    print(f"  {'Component':<18} {'State':<32} {'Unconstrained %':>18} {'Constrained %':>15} {'z-score':>10}")
    print("  " + "-" * 106)
    for r in sig_single_suppressed:
        print(f"  {r['component']:<18} {r['state']:<32} {r['p1']:>17.2%} {r['p2']:>14.2%} {r['z']:>10.2f}")
        
    print("\nBOOSTED STATES (forced or increased in constrained model):")
    print("-" * 110)
    print(f"  {'Component':<18} {'State':<32} {'Unconstrained %':>18} {'Constrained %':>15} {'z-score':>10}")
    print("  " + "-" * 106)
    for r in sig_single_boosted:
        print(f"  {r['component']:<18} {r['state']:<32} {r['p1']:>17.2%} {r['p2']:>14.2%} {r['z']:>10.2f}")
        
    # --- PART 2: PAIRWISE (CO-OCCURRENCE) DEVIATIONS ---
    print("\n" + "=" * 80)
    print("PART 2: PAIRWISE (CO-OCCURRENCE) DEVIATIONS")
    print("=" * 80)
    
    common_pairs = []
    total_pairs = 0
    for comp_x, comp_y in product(COMPONENTS, repeat=2):
        if comp_x == comp_y:
            continue
        for sx in states1[comp_x]:
            for sy in states1[comp_y]:
                total_pairs += 1
                common_pairs.append((comp_x, comp_y, sx, sy))
                
    bonf_alpha_pair = alpha / total_pairs
    bonf_z_pair = norm.ppf(1 - bonf_alpha_pair / 2)
    print(f"Total pairs: {total_pairs}, Bonferroni-corrected alpha: {bonf_alpha_pair:.6f}, Critical z: {bonf_z_pair:.2f}")
    
    pair_results = []
    for comp_x, comp_y, sx, sy in common_pairs:
        x1 = pairs1.get((sx, sy), 0)
        p1 = x1 / N1
        x2 = pairs2.get((sx, sy), 0)
        p2 = x2 / N2
        
        p_pool = (x1 + x2) / (N1 + N2)
        if p_pool == 0 or p_pool == 1:
            z = 0.0
        else:
            se = math.sqrt(p_pool * (1 - p_pool) * (1/N1 + 1/N2))
            z = (p2 - p1) / se if se > 0 else 0.0
            
        pair_results.append({
            'comp_x': comp_x, 'state_x': sx,
            'comp_y': comp_y, 'state_y': sy,
            'p1': p1, 'p2': p2, 'z': z,
            'sig': abs(z) > bonf_z_pair
        })
        
    sig_pair_suppressed = sorted([r for r in pair_results if r['z'] < 0 and r['sig']], key=lambda r: r['z'])
    sig_pair_boosted = sorted([r for r in pair_results if r['z'] > 0 and r['sig']], key=lambda r: r['z'], reverse=True)
    
    print(f"\nSignificant pairwise deviations: {len([r for r in pair_results if r['sig']])} of {total_pairs}")
    print(f"  Suppressed: {len(sig_pair_suppressed)}")
    print(f"  Boosted:    {len(sig_pair_boosted)}")
    
    if sig_pair_boosted:
        print("\nTOP 20 MOST BOOSTED CO-OCCURRENCES:")
        print("-" * 110)
        print(f"  {'State X':<32} {'State Y':<32} {'Unconstrained %':>15} {'Constrained %':>15} {'z-score':>10}")
        print("  " + "-" * 106)
        for r in sig_pair_boosted[:20]:
            print(f"  {r['state_x']:<32} {r['state_y']:<32} {r['p1']:>14.2%} {r['p2']:>14.2%} {r['z']:>10.2f}")

if __name__ == "__main__":
    main()
