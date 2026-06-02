import sqlite3
conn = sqlite3.connect('bill_list.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cur.fetchall()
print('=== ALL TABLES ===')
for t in tables:
    name = t[0]
    print(f'\nTable: {name}')
    cur.execute(f'PRAGMA table_info("{name}")')
    cols = cur.fetchall()
    for c in cols:
        nullable = 'NO' if c[3] else 'YES'
        print(f'  {c[1]:30s} {c[2]:15s} NOT_NULL={nullable}  DEFAULT={c[4]}')
    cur.execute(f'SELECT COUNT(*) FROM "{name}"')
    cnt = cur.fetchone()[0]
    print(f'  [Row count: {cnt}]')
print('\n\n=== STAFF TABLE DATA ===')
cur.execute('SELECT * FROM staff')
for row in cur.fetchall():
    print(f'  {row}')
print('\n=== staff_assignments DATA ===')
cur.execute('SELECT * FROM staff_assignments')
for row in cur.fetchall():
    print(f'  {row}')
print('\n=== auto_assignment_rules DATA ===')
cur.execute('SELECT * FROM auto_assignment_rules')
for row in cur.fetchall():
    print(f'  {row}')
conn.close()
