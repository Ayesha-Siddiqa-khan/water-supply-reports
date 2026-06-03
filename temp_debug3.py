import sqlite3
conn = sqlite3.connect("E:\\water suppy report\\water suppy report\\bill_list.sqlite3")
conn.row_factory = sqlite3.Row

# Check arrears for bills
print("=== Bills with amount_received > 0 for Gulberg/Bahu ===")
for r in conn.execute("""
    SELECT sector, locality, connection_no, amount_received, arrears, consumer_name
    FROM bills 
    WHERE (sector LIKE '%Bahu%' OR sector LIKE '%Gulberg%') 
    AND amount_received > 0
    ORDER BY sector, connection_no
"""):
    print(f"  sector={r['sector']!r} locality={r['locality']!r} conn={r['connection_no']!r} amt={r['amount_received']} arrears={r['arrears']} name={r['consumer_name']!r}")

print("\n=== Summarized: all bills with amount_received > 0 by sector/locality ===")
for r in conn.execute("""
    SELECT sector, locality, COUNT(*) as count, SUM(amount_received) as total_amt, SUM(arrears) as total_arr
    FROM bills
    WHERE amount_received > 0
    GROUP BY sector, locality
    ORDER BY sector, locality
"""):
    print(f"  sector={r['sector']!r} locality={r['locality']!r} count={r['count']} amt={r['total_amt']} arr={r['total_arr']}")

print("\n=== All bills grouped by sector (amount > 0) ===")
for r in conn.execute("""
    SELECT sector, COUNT(*) as count, SUM(amount_received) as total_amt, SUM(arrears) as total_arr
    FROM bills
    WHERE amount_received > 0
    GROUP BY sector
    ORDER BY sector
"""):
    print(f"  sector={r['sector']!r} count={r['count']} amt={r['total_amt']} arr={r['total_arr']}")
