import sqlite3
conn = sqlite3.connect("data/smart_home_composed_scope2_traces.db")
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM traces')
N = cur.fetchone()[0]
print(f'Total traces: {N}')

print('\nHEMS states:')
cur.execute('SELECT hems, COUNT(*) FROM trace_states GROUP BY hems ORDER BY COUNT(*) DESC')
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]} ({r[1]/N*100:.1f}%)')

print('\nGrid states:')
cur.execute('SELECT grid_connection, COUNT(*) FROM trace_states GROUP BY grid_connection ORDER BY COUNT(*) DESC')
for r in cur.fetchall(): print(f'  {r[0]}: {r[1]} ({r[1]/N*100:.1f}%)')

print('\nSignal 2:')
cur.execute("""SELECT optional_event,
    SUM(CASE WHEN is_present=1 THEN 1 ELSE 0 END) as p,
    SUM(CASE WHEN is_present=0 THEN 1 ELSE 0 END) as a
    FROM signal2 GROUP BY optional_event""")
for r in cur.fetchall():
    print(f'  {r[0]:<25} present={r[1]:>6}  absent={r[2]:>6}  ({r[2]/(r[1]+r[2])*100:.1f}% vacuous)')

print('\nDR event + loads_shed_for_dr:')
cur.execute("SELECT COUNT(*) FROM trace_states WHERE grid_connection='demand response event' AND thermal_loads='loads shed for dr'")
print(f'  Co-occurrence: {cur.fetchone()[0]}')

print('\nGrid services mode traces:')
cur.execute("SELECT COUNT(*) FROM trace_states WHERE hems='grid services mode'")
print(f'  grid_services_mode: {cur.fetchone()[0]}')

conn.close()
