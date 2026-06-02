import sqlite3

conn = sqlite3.connect('bill_list.sqlite3')
cur = conn.cursor()

cur.execute('SELECT COUNT(*) FROM bills')
print('Total bills:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM bills WHERE connection_no != "" AND connection_no IS NOT NULL')
print('Bills with connection_no:', cur.fetchone()[0])

cur.execute('SELECT COUNT(DISTINCT connection_no) FROM bills WHERE connection_no != "" AND connection_no IS NOT NULL')
print('Distinct connections:', cur.fetchone()[0])

cur.execute('SELECT connection_no, COUNT(*) as cnt FROM bills WHERE connection_no != "" AND connection_no IS NOT NULL GROUP BY connection_no HAVING cnt > 1 LIMIT 10')
print('\nDuplicate connections (showing top 10):')
for row in cur.fetchall():
    print(f'  {row[0]}: {row[1]} times')

conn.close()