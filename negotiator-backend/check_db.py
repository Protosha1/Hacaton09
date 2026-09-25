import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=" * 50)
print("ТАБЛИЦЫ В БД:")
print("=" * 50)
for t in tables:
    print(f"  ✓ {t[0]}")

for table_name in ["users", "scenarios", "negotiation_sessions", "messages", "analysis_reports"]:
    print()
    print("=" * 50)
    print(f"СТРУКТУРА: {table_name}")
    print("=" * 50)
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    if not columns:
        print(f"  ⚠️ Таблица '{table_name}' не найдена!")
        continue
    
    for col in columns:
        col_id, name, col_type, notnull, default, is_pk = col
        flags = []
        if is_pk:
            flags.append("PK")
        if notnull:
            flags.append("NOT NULL")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(f"  - {name}: {col_type}{flag_str}")

conn.close()
print()
print("Готово.")