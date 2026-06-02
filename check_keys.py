import sqlite3
import pandas as pd

# Check database bill_keys
conn = sqlite3.connect('bill_list.sqlite3')
cur = conn.cursor()
cur.execute('SELECT bill_key, COUNT(*) as cnt FROM bills GROUP BY bill_key HAVING cnt > 1')
dups = cur.fetchall()
print(f'Duplicate bill_keys in DB: {len(dups)}')
if dups:
    for d in dups[:5]:
        print(f'  {d[0][:50]}... : {d[1]} times')
conn.close()

# Check CSV bill keys
df = pd.read_csv('Bills-15-05-2026-08_11_13.csv')
print(f'\nCSV has {len(df)} rows')
print(f'Unique Bill No: {df["Bill No"].nunique()}')

# Check if there are empty Bill No
empty_bills = df['Bill No'].isna().sum() + (df['Bill No'] == '').sum()
print(f'Empty Bill No: {empty_bills}')