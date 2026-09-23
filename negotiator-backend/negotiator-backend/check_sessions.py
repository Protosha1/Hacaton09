import sqlite3

conn = sqlite3.connect("app.db")

print("Sessions:")
for row in conn.execute(
    "SELECT id, scenario_id, user_id, status FROM negotiation_sessions"
):
    print(" ", row)

conn.close()