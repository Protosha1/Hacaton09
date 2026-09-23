import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("SELECT id, email, name, CASE WHEN hashed_password IS NULL THEN 'NO PASSWORD' ELSE 'HAS PASSWORD' END FROM users")
print("Users in DB:")
for row in cursor.fetchall():
    print(f"  email={row[1]}  name={row[2]}  {row[3]}")
conn.close()