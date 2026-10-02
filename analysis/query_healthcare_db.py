import sqlite3

DB_FILE = "data/healthcare_traces.db"

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Query counts of physician prescribing in both
cur.execute("SELECT COUNT(*) FROM trace_states_unconstrained WHERE physician = 'physician prescribing'")
p1 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM trace_states_constrained WHERE physician = 'physician prescribing'")
p2 = cur.fetchone()[0]

print(f"physician prescribing: unconstrained = {p1}/729, constrained = {p2}/36")

# Query counts of pharmacy filling in both
cur.execute("SELECT COUNT(*) FROM trace_states_unconstrained WHERE pharmacy = 'pharmacy filling'")
ph1 = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM trace_states_constrained WHERE pharmacy = 'pharmacy filling'")
ph2 = cur.fetchone()[0]

print(f"pharmacy filling: unconstrained = {ph1}/729, constrained = {ph2}/36")

# Query counts of co-occurrence
cur.execute("""
    SELECT COUNT(*) FROM trace_states_unconstrained 
    WHERE physician = 'physician prescribing' AND pharmacy = 'pharmacy filling'
""")
pair1 = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*) FROM trace_states_constrained 
    WHERE physician = 'physician prescribing' AND pharmacy = 'pharmacy filling'
""")
pair2 = cur.fetchone()[0]

print(f"prescribing & filling: unconstrained = {pair1}/729, constrained = {pair2}/36")

# Query all states in constrained to see what actually co-occurs
cur.execute("SELECT DISTINCT patient, clinical_device, ehr_system, physician, pharmacy, insurance FROM trace_states_constrained")
print("\nUnique traces in constrained model:")
for i, row in enumerate(cur.fetchall()):
    print(f"  {i+1}: {row}")

conn.close()
