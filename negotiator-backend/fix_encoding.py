import os

for root, dirs, files in os.walk("."):
    # Пропускаем виртуальное окружение и git
    if "venv" in root or ".git" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                # Читаем в windows-1251 / cp1251
                with open(path, "r", encoding="cp1251") as f:
                    content = f.read()
                # Перезаписываем в utf-8
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Исправлен: {path}")
            except Exception as e:
                pass