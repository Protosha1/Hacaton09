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
# fix_encoding.py
"""
Fix encoding issues in .py files:
  1. UTF-8 BOM (EF BB BF) -> strip
  2. Corrupted BOM (literal "п»ї" from cp1251) -> strip
  3. Files entirely in Windows-1251 -> convert to UTF-8

Usage:
  python fix_encoding.py
  python fix_encoding.py --check    # only report, do not modify
"""
import sys
from pathlib import Path


# Byte patterns of the corrupted BOM in UTF-8 encoding
# "п" = D0 BF, "»" = C2 BB, "ї" = D1 97
CORRUPTED_BOM_UTF8 = b"\xd0\xbf\xc2\xbb\xd1\x97"
UTF8_BOM = b"\xef\xbb\xbf"

# Folder names to skip
SKIP_DIRS = {"__pycache__", ".pytest_cache", "venv", ".venv", "env", "ENV"}

# File extensions to check
EXTENSIONS = {".py", ".ini", ".md", ".txt", ".yml", ".yaml", ".toml", ".cfg"}


def try_decode_utf8(data: bytes) -> str | None:
    """Return decoded text or None if not valid UTF-8."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def strip_bom_prefix(data: bytes) -> tuple[bytes, bool]:
    """Remove UTF-8 BOM or its corrupted variant from the start."""
    changed = False
    # Plain UTF-8 BOM
    if data.startswith(UTF8_BOM):
        data = data[len(UTF8_BOM):]
        changed = True
    # Corrupted BOM (literal "п»ї")
    if data.startswith(CORRUPTED_BOM_UTF8):
        data = data[len(CORRUPTED_BOM_UTF8):]
        changed = True
    return data, changed


def convert_cp1251(data: bytes) -> str:
    """Decode bytes as Windows-1251 and return text."""
    return data.decode("cp1251")


def fix_file(path: Path, check_only: bool) -> str:
    """
    Return one of: 'ok', 'bom', 'cp1251', 'skip'.
    Modifies the file unless check_only is True.
    """
    try:
        data = path.read_bytes()
    except OSError as e:
        return f"skip (read error: {e})"

    if not data:
        return "skip (empty)"

    # Step 1: strip BOM prefix
    data_after_bom, bom_changed = strip_bom_prefix(data)

    # Step 2: check if content is valid UTF-8
    utf8_text = try_decode_utf8(data_after_bom)

    if utf8_text is not None:
        # Valid UTF-8
        if bom_changed:
            if not check_only:
                path.write_bytes(data_after_bom)
            return "bom"
        return "ok"

    # Step 3: not valid UTF-8 -> try cp1251
    try:
        text = convert_cp1251(data)
    except Exception as e:
        return f"skip (unknown encoding: {e})"

    if not check_only:
        path.write_text(text, encoding="utf-8")
    return "cp1251"


def iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in EXTENSIONS:
            continue
        yield p


def main():
    check_only = "--check" in sys.argv
    root = Path(".")

    fixed_bom = []
    fixed_cp = []
    ok_count = 0
    skipped = []

    for path in iter_files(root):
        rel = path.relative_to(root)
        result = fix_file(path, check_only=check_only)

        if result == "ok":
            ok_count += 1
        elif result == "bom":
            fixed_bom.append(str(rel))
        elif result == "cp1251":
            fixed_cp.append(str(rel))
        elif result.startswith("skip"):
            skipped.append(f"{rel}  ({result})")

    print("=" * 60)
    if check_only:
        print("CHECK MODE - no files were modified")
    else:
        print("FIX MODE")
    print("=" * 60)
    print(f"Already clean: {ok_count}")

    if fixed_bom:
        print(f"\nBOM stripped ({len(fixed_bom)}):")
        for f in fixed_bom:
            print(f"  {f}")

    if fixed_cp:
        print(f"\nConverted from cp1251 ({len(fixed_cp)}):")
        for f in fixed_cp:
            print(f"  {f}")

    if skipped:
        print(f"\nSkipped ({len(skipped)}):")
        for s in skipped:
            print(f"  {s}")

    total_fixed = len(fixed_bom) + len(fixed_cp)
    print()
    if check_only:
        print(f"Would fix: {total_fixed} file(s)")
        if total_fixed > 0:
            print("Run without --check to apply fixes.")
    else:
        print(f"Fixed: {total_fixed} file(s)")


if __name__ == "__main__":
    main()