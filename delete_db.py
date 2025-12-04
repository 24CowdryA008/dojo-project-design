import os

db_locale = 'users.db'
if os.path.exists(db_locale):
    os.remove(db_locale)
    print("users.db deleted successfully.")
else:
    print("users.db does not exist.")