#!/usr/bin/env python3
"""Watch source spreadsheets and rebuild app JSON after each save."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
LOCAL_APP: Path | None = None
NO_LOCAL_SYNC = False
WATCHED = (
    ROOT / "source" / "asana_catalog_v1.xlsx",
    ROOT / "source" / "asana_catalog_v1.csv",
    ROOT / "source" / "asana_names_study.xlsx",
    ROOT / "source" / "asana_names_study.csv",
)


def snapshot(paths: tuple[Path, ...]) -> dict[Path, float]:
    return {path: path.stat().st_mtime for path in paths if path.exists()}


def run_step(label: str, args: list[str]) -> bool:
    print(f"\n{label}")
    completed = subprocess.run(args, cwd=ROOT)
    return completed.returncode == 0


def rebuild() -> None:
    generate_args = [sys.executable, "tools/generate_asanas.py"]
    if LOCAL_APP:
        generate_args.extend(["--local-app", str(LOCAL_APP)])
    if NO_LOCAL_SYNC:
        generate_args.append("--no-local-sync")

    ok = run_step("Сборка JSON из Excel/CSV...", generate_args)
    if ok:
        run_step("Проверка данных...", [sys.executable, "tools/validate_data.py"])


def main() -> int:
    global LOCAL_APP, NO_LOCAL_SYNC

    parser = argparse.ArgumentParser(description="Следить за source/*.xlsx и source/*.csv.")
    parser.add_argument("--interval", type=float, default=2.0, help="Интервал проверки в секундах")
    parser.add_argument("--local-app", type=Path, default=None, help="Дополнительная локальная папка приложения")
    parser.add_argument("--no-local-sync", action="store_true", help="Не копировать JSON в локальную папку приложения")
    args = parser.parse_args()
    LOCAL_APP = args.local_app
    NO_LOCAL_SYNC = args.no_local_sync

    print("Namaskar watcher запущен. Нажмите Ctrl+C, чтобы остановить.")
    print("Отслеживаются:")
    for path in WATCHED:
        print(f"  - {path}")

    last = snapshot(WATCHED)
    rebuild()
    try:
        while True:
            time.sleep(args.interval)
            current = snapshot(WATCHED)
            if current != last:
                last = current
                rebuild()
    except KeyboardInterrupt:
        print("\nWatcher остановлен.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
