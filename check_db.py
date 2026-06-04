import sqlite3

conn = sqlite3.connect("retail_analytics.db")
cursor = conn.cursor()

# Check if table exists
cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table'
""")

print("Tables:")
print(cursor.fetchall())

# Count rows
cursor.execute("SELECT COUNT(*) FROM events")
count = cursor.fetchone()[0]

print(f"\nRows in database: {count}")

# Show all rows
cursor.execute("SELECT * FROM events")

rows = cursor.fetchall()

print("\nData:")

for row in rows:
    print(row)

cursor.execute("SELECT COUNT(*) FROM transactions")

print("Transactions:")
print(cursor.fetchone()[0])

conn.close()