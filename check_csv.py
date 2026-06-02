import pandas as pd

df = pd.read_csv('Bills-15-05-2026-08_11_13.csv')
print(f'CSV rows: {len(df)}')
print(f'CSV columns: {list(df.columns)}')

if 'Bill No' in df.columns:
    print(f'\nDuplicate Bill No: {df["Bill No"].duplicated().sum()}')
    print(f'Distinct Bill No: {df["Bill No"].nunique()}')
elif 'Connection No' in df.columns:
    print(f'\nDuplicate Connection No: {df["Connection No"].duplicated().sum()}')
    print(f'Distinct Connection No: {df["Connection No"].nunique()}')