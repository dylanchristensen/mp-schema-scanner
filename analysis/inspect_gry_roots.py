import json

def inspect_gry(path):
    print(f"\nInspecting {path}:")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    graphs = data.get("graphs", [])
    for g in graphs:
        trace = g.get("trace")
        if trace is None:
            continue
        nodes = trace.get("nodes", [])
        edges = trace.get("edges", [])
        
        parent_map = {}
        for edge in edges:
            if edge.get("relation") == "IN":
                parent_map[edge["to_id"]] = edge["from_id"]
                
        node_map = {n["id"]: n for n in nodes}
        
        roots = [n for n in nodes if n["type"] == "R"]
        choices = [n for n in nodes if n["type"] == "C"]
        
        print("Roots:")
        for r in roots:
            print(f"  {r['label']}")
            
        print("Choices and their parents:")
        for c in choices[:15]:
            pid = parent_map.get(c["id"])
            p_label = node_map[pid]["label"] if pid and pid in node_map else "None"
            print(f"  {c['label']} (Parent: {p_label})")
            
        break

inspect_gry("data/constrained.gry")
