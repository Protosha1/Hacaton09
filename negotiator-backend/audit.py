# audit.py
import re
from pathlib import Path


ok_count = 0
fail_count = 0


def check(label: str, condition: bool, detail: str = ""):
    global ok_count, fail_count
    if condition:
        ok_count += 1
        print(f"[OK]   {label}{(' - ' + detail) if detail else ''}")
    else:
        fail_count += 1
        print(f"[FAIL] {label}{(' - ' + detail) if detail else ''}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


root = Path("app")

# 1. Ownership check
neg_api = read(root / "api" / "v1" / "negotiation.py")
check(
    "Ownership check in negotiation API",
    "_ensure_session_owner" in neg_api and "session.user_id != user.id" in neg_api,
)

# 2. user_id from token
check(
    "user_id from token (not body) in /start",
    "user_id=user.id" in neg_api,
)

# 3. SECRET_KEY default
cfg = read(root / "core" / "config.py")
check(
    "SECRET_KEY has no weak default",
    "change-me-in-production" not in cfg,
)

# 4. CORS
main_py = read(root / "main.py")
check(
    "CORS: no wildcard + credentials combo",
    not ('allow_origins=["*"]' in main_py and "allow_credentials=True" in main_py),
)

# 5. End-of-dialog detection
neg_svc = read(root / "services" / "negotiation_service.py")
check(
    "End-of-dialog uses explicit marker",
    "SESSION_END" in neg_svc and "we have a deal" not in neg_svc,
)

# 6. LLM errors as exceptions
llm = read(root / "services" / "llm_service.py")
check(
    "LLMService raises exception (not returns string)",
    "raise LLMError" in llm or "class LLMError" in llm,
)

# 7. Whisper model size
voice = read(root / "services" / "voice_service.py")
check(
    "Whisper uses model 'small' or 'base' (not 'medium')",
    '"small"' in voice or '"base"' in voice,
)

# 8. datetime tz
utcnow_count = 0
for py in root.rglob("*.py"):
    text = read(py)
    utcnow_count += text.count("datetime.utcnow")
check("No deprecated datetime.utcnow()", utcnow_count == 0)

# 9. requirements: no junk
req = read(Path("requirements.txt"))
check("No openrouter in requirements", "openrouter" not in req.lower())
check("No passlib in requirements", "passlib" not in req.lower())

# 10. .dockerignore
check(".dockerignore exists (not .dockerignore.txt)", Path(".dockerignore").exists())

print()
print(f"Итого: {ok_count} OK, {fail_count} FAIL")