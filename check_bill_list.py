import sqlite3

conn = sqlite3.connect('bill_list.sqlite3')
cur = conn.cursor()

# Check summary
cur.execute("""
    SELECT
        COUNT(*) AS total_bills,
        COUNT(DISTINCT NULLIF(connection_no, '')) AS total_connections,
        SUM(CASE WHEN amount_received > 0 THEN 1 ELSE 0 END) AS received_bills
    FROM bills
""")
row = cur.fetchone()
print(f"Total bills (count all): {row[0]}")
print(f"Total connections (distinct): {row[1]}")
print(f"Received bills: {row[2]}")

# Check sector-wise breakdown total
cur.execute("SELECT SUM(total_bills) FROM (SELECT sector, COUNT(*) as total_bills FROM bills GROUP BY sector)")
print(f"\nSum of sector counts: {cur.fetchone()[0]}")

conn.close()