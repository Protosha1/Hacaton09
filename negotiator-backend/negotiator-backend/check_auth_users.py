import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("SELECT id, email, name, substr(hashed_password, 1, 20) FROM users")
print("Users in DB:")
for row in cursor.fetchall():
    print(f"  id={row[0]}")
    print(f"  email={row[1]}")
    print(f"  name={row[2]}")
    print(f"  hash={row[3]}...")
    print()
conn.close()