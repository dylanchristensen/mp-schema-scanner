import json

def inspect_edges(path):
    print(f"\nInspecting edges in {path}:")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    graphs = data.get("graphs", [])
    for g in graphs:
        trace = g.get("trace")
        if trace is None:
            continue
        edges = trace.get("edges", [])
        nodes = trace.get("nodes", [])
        node_map = {n["id"]: n for n in nodes}
        
        print(f"Total edges: {len(edges)}")
        relations = set(e.get("relation") for e in edges)
        print(f"Unique relation types: {relations}")
        
        print("\nFirst 20 edges:")
        for edge in edges[:20]:
            from_label = node_map.get(edge["from_id"], {}).get("label", "unknown")
            from_type = node_map.get(edge["from_id"], {}).get("type", "?")
            to_label = node_map.get(edge["to_id"], {}).get("label", "unknown")
            to_type = node_map.get(edge["to_id"], {}).get("type", "?")
            print(f"  ({from_type}) {from_label} -- [{edge.get('relation')}] --> ({to_type}) {to_label}")
            
        break

inspect_edges("data/healthcareDelivery_scope_1.gry")
