import sqlite3

conn = sqlite3.connect("bookings.db")
c = conn.cursor()

print("\nTABLE STRUCTURE:")
c.execute("PRAGMA table_info(bookings);")
for row in c.fetchall():
    print(row)

print("\nDATA IN TABLE:")
c.execute("SELECT * FROM bookings;")
for row in c.fetchall():
    print(row)

conn.close()
