# install_nodejs.py
"""
Install Node.js LTS on Windows without admin rights.

Downloads the official portable ZIP from nodejs.org, extracts to
%LOCALAPPDATA%\Programs\nodejs, and adds it to the user PATH.

Usage:
    python install_nodejs.py
    python install_nodejs.py --version 22.14.0
    python install_nodejs.py --target D:\\tools\\nodejs
    python install_nodejs.py --uninstall
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import winreg
import zipfile
from pathlib import Path


DEFAULT_VERSION = "22.14.0"
DIST_BASE = "https://nodejs.org/dist"
DEFAULT_TARGET = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Programs" / "nodejs"


# ---------- PATH via registry (user scope, no admin) ----------

def read_user_path() -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            value, _ = winreg.QueryValueEx(key, "Path")
            return value
    except FileNotFoundError:
        return ""


def write_user_path(value: str) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, value)


def normalize(p: str) -> str:
    return p.strip().rstrip("\\").lower()


def add_to_user_path(folder: Path) -> bool:
    target = str(folder)
    current = read_user_path()
    parts = [p for p in current.split(";") if p.strip()]
    if any(normalize(p) == normalize(target) for p in parts):
        return False
    parts.append(target)
    write_user_path(";".join(parts))
    return True


def remove_from_user_path(folder: Path) -> bool:
    target = str(folder)
    current = read_user_path()
    parts = [p for p in current.split(";") if p.strip()]
    kept = [p for p in parts if normalize(p) != normalize(target)]
    if len(kept) == len(parts):
        return False
    write_user_path(";".join(kept))
    return True


# ---------- Download and extract ----------

def download(url: str, dest: Path) -> None:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as out:
        total = r.length or 0
        done = 0
        while True:
            chunk = r.read(256 * 1024)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done * 100 // total:3d}%  ({done // (1024*1024)} MB)", end="")
        print()


def extract(zip_path: Path, target: Path) -> None:
    print(f"Extracting to {target}")

    staging = target.parent / f"{target.name}__staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(staging)

    entries = [p for p in staging.iterdir()]
    if len(entries) != 1 or not entries[0].is_dir():
        raise RuntimeError(f"Unexpected archive layout: {[p.name for p in entries]}")

    if target.exists():
        shutil.rmtree(target)

    entries[0].rename(target)
    shutil.rmtree(staging, ignore_errors=True)


# ---------- Verify ----------

def verify(target: Path) -> bool:
    node_exe = target / "node.exe"
    npm_cmd = target / "npm.cmd"

    if not node_exe.exists():
        print(f"[FAIL] node.exe not found in {target}")
        return False
    if not npm_cmd.exists():
        print(f"[FAIL] npm.cmd not found in {target}")
        return False

    print(f"  node.exe: {node_exe} ({node_exe.stat().st_size} bytes)")
    print(f"  npm.cmd:  {npm_cmd} ({npm_cmd.stat().st_size} bytes)")

    try:
        out = subprocess.check_output(
            [str(node_exe), "--version"], text=True, stderr=subprocess.STDOUT
        ).strip()
        print(f"  node --version: {out}")
    except Exception as e:
        print(f"[FAIL] Cannot run node.exe: {e}")
        return False

    return True


# ---------- Commands ----------
def do_install(args) -> None:
    target: Path = Path(args.target).expanduser().resolve() if args.target else DEFAULT_TARGET

    print("=" * 60)
    print("  Portable Node.js install (no admin)")
    print(f"  Version: {args.version}")
    print(f"  Target:  {target}")
    print("=" * 60)

    if (target / "node.exe").exists():
        print("\n[INFO] Node.js already present.")
        add_to_user_path(target)
        verify(target)
        print("\nIf 'node' is not found in a new terminal, restart Windows Explorer")
        print("or reboot. Alternatively, use full path:")
        print(f'  "{target}\\npm.cmd" install')
        return

    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="nodejs_dl_") as tmp:
        zip_path = Path(tmp) / f"node-v{args.version}-win-x64.zip"
        url = f"{DIST_BASE}/v{args.version}/node-v{args.version}-win-x64.zip"
        download(url, zip_path)
        extract(zip_path, target)

    added = add_to_user_path(target)
    if added:
        print(f"\nAdded to user PATH: {target}")
    else:
        print(f"\nAlready in user PATH: {target}")

    print("\nVerifying ...")
    if not verify(target):
        sys.exit(1)

    print("\n[OK] Node.js installed.")
    print()
    print("To use it in this terminal session:")
    print(f'  set "PATH={target};%PATH%"')
    print()
    print("Then:")
    print('  npm install')
    print()
    print("In a brand-new terminal, PATH should work automatically.")
    print("If not — restart Windows Explorer or reboot.")


def do_uninstall(args) -> None:
    target: Path = Path(args.target).expanduser().resolve() if args.target else DEFAULT_TARGET

    if remove_from_user_path(target):
        print(f"Removed from user PATH: {target}")
    else:
        print("Not in user PATH.")

    if target.exists():
        print(f"Deleting {target} ...")
        shutil.rmtree(target, ignore_errors=True)
        print("Done.")
    else:
        print("Folder does not exist.")


def main():
    if sys.platform != "win32":
        sys.exit("[ERROR] Windows only.")

    ap = argparse.ArgumentParser(description="Portable Node.js install, no admin.")
    ap.add_argument("--version", default=DEFAULT_VERSION)
    ap.add_argument("--target", default=None)
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()

    if args.uninstall:
        do_uninstall(args)
    else:
        do_install(args)


if __name__ == "__main__":
    main()