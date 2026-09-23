# check_seed.py
import sqlite3

conn = sqlite3.connect("app.db")

print("Пользователи:")
for row in conn.execute("SELECT id, email, name FROM users"):
    print(" ", row)

print("\nСценарии:")
for row in conn.execute("SELECT id, name FROM scenarios"):
    print(" ", row)

conn.close()