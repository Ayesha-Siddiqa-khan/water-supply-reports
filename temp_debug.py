import sqlite3, json
conn = sqlite3.connect("E:\\water suppy report\\water suppy report\\bill_list.sqlite3")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT DISTINCT sector, locality, zone FROM bills ORDER BY sector, locality").fetchall()
print(f"Total distinct combinations: {len(rows)}")
for r in rows:
    print(f"  sector={r['sector']!r}, locality={r['locality']!r}, zone={r['zone']!r}")

print("\n=== Staff assignments ===")
rows2 = conn.execute("SELECT sa.*, s.name as staff_name FROM staff_assignments sa JOIN staff s ON s.id = sa.staff_id ORDER BY s.name").fetchall()
for r in rows2:
    print(f"  staff={r['staff_name']!r} zone={r['zone']!r} sector={r['sector']!r} locality={r['locality']!r}")

print("\n=== Localities zones (for key sectors) ===")
for search in ["Bahu", "Gulberg", "Ghaziani", "Sabz", "Sabzi"]:
    rows3 = conn.execute("SELECT sector, locality, zone FROM localities WHERE sector LIKE ? OR locality LIKE ?", (f"%{search}%", f"%{search}%")).fetchall()
    for r in rows3:
        print(f"  sector={r['sector']!r}, locality={r['locality']!r}, zone={r['zone']!r}")
