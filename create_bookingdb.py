# create_bookings_db.py
import sqlite3

conn = sqlite3.connect("bookings.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    course TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("bookings.db created.")
