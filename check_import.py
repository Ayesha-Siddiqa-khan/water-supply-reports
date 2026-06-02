import sqlite3

conn = sqlite3.connect('bill_list.sqlite3')
cur = conn.cursor()

# Check all bill imports with timestamps
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%bill%'")
print('Tables:', cur.fetchall())

# Check when bills were inserted (if there's any timestamp)
cur.execute("SELECT COUNT(*), MIN(rowid), MAX(rowid) FROM bills")
print(f'\nBill rowids - min: {cur.fetchone()[1]}, max: {cur.fetchone()[2]}')

# Check for any import metadata
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('All tables:', tables)

conn.close()