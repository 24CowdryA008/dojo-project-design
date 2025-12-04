import sqlite3
def create_database():
    db_locale = 'users.db'

    connection = sqlite3.connect(db_locale)
    cursor = connection.cursor()

    cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forename TEXT NOT NULL,
    surname TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
    ''')

    connection.commit()
    connection.close()

create_database()
print("Database and users table created successfully.")