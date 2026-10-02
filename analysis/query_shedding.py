import sqlite3
conn = sqlite3.connect("data/smart_home_composed_scope2_traces.db")
cur = conn.cursor()
cur.execute("SELECT COUNT(1) FROM trace_states WHERE thermal_loads='loads shed for dr'")
n_shed = cur.fetchone()[0]

cur.execute("SELECT COUNT(1) FROM trace_states WHERE thermal_loads='loads shed for dr' AND hems='manual override mode'")
n_shed_manual = cur.fetchone()[0]

cur.execute("SELECT COUNT(1) FROM trace_states WHERE thermal_loads='loads shed for dr' AND grid_connection='demand response event'")
n_shed_dr = cur.fetchone()[0]

print(f'Total loads shed: {n_shed}')
print(f'With manual override: {n_shed_manual}')
print(f'With DR event: {n_shed_dr}')
conn.close()
