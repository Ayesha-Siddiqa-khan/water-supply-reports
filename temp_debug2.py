import sqlite3

conn = sqlite3.connect("E:\\water suppy report\\water suppy report\\bill_list.sqlite3")
conn.row_factory = sqlite3.Row

print("=== SECTORS table ===")
for r in conn.execute("SELECT * FROM sectors ORDER BY name, zone"):
    print(f"  name={r['name']!r} zone={r['zone']!r}")

print("\n=== Staff assignments for IRFAN/TAHIR ===")
for r in conn.execute("""
    SELECT sa.*, s.name as staff_name
    FROM staff_assignments sa
    JOIN staff s ON s.id = sa.staff_id
    WHERE s.name IN ('MUHAMMAD IRFAN', 'MUHAMMAD TAHIR')
"""):
    print(f"  staff={r['staff_name']!r} zone={r['zone']!r} sector={r['sector']!r} locality={r['locality']!r}")

print("\n=== ALL bills (sector, locality, zone) for matching keys ===")
bills = conn.execute("""
    SELECT sector, locality, zone, connection_no, amount_received
    FROM bills
    WHERE sector LIKE '%Bahu%' OR sector LIKE '%Gulberg%' OR sector LIKE '%Ghaziani%'
    ORDER BY sector, locality
""").fetchall()
for r in bills:
    print(f"  sector={r['sector']!r} locality={r['locality']!r} zone={r['zone']!r} conn={r['connection_no']!r} amt={r['amount_received']}")

print("\n=== All Unassigned zone bills ===")
for r in conn.execute("SELECT sector, locality, zone, connection_no, amount_received, arrears FROM bills WHERE zone = 'Unassigned'"):
    print(f"  sector={r['sector']!r} locality={r['locality']!r} conn={r['connection_no']!r} amt={r['amount_received']!r} arr={r['arrears']!r}")

print("\n=== Check zones for Gulberg/Bahu locality entries ===")
for r in conn.execute("SELECT * FROM localities WHERE sector LIKE '%Bahu%' OR sector LIKE '%Gulberg%' OR sector LIKE '%Ghaziani%'"):
    print(f"  sector={r['sector']!r} locality={r['locality']!r} zone={r['zone']!r}")
