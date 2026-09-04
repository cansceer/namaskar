#!/usr/bin/env python3
"""Create human-readable study files from data/study.json."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "source"
FIELDS = (
    ("ID", "id"),
    ("Оригинальное название", "sanskrit"),
    ("Транслитерация на русском", "transliteration"),
    ("Популярное название", "ru"),
    ("По слогам для чтения", "syllables"),
    ("Разбор по частям", "parts"),
    ("Буквальный смысл", "literal"),
    ("От чего произошло", "origin"),
    ("Подсказка для запоминания", "memory"),
    ("Раздел", "section"),
)


def main() -> int:
    study = json.loads((ROOT / "data" / "study.json").read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = OUT_DIR / "asana_names_study.generated.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[title for title, _key in FIELDS])
        writer.writeheader()
        for item in study:
            writer.writerow({title: item.get(key, "") for title, key in FIELDS})

    md_path = OUT_DIR / "asana_names_study.generated.md"
    lines = ["# Изучение названий асан", ""]
    current_section = None
    for item in study:
        section = item.get("section", "Без раздела")
        if section != current_section:
            current_section = section
            lines.extend([f"## {section}", ""])
        lines.extend(
            [
                f"### {item.get('sanskrit', '')} - {item.get('ru', '')}",
                f"- Транслитерация: {item.get('transliteration', '')}",
                f"- По слогам: {item.get('syllables', '')}",
                f"- Разбор: {item.get('parts', '')}",
                f"- Буквально: {item.get('literal', '')}",
                f"- Происхождение: {item.get('origin', '')}",
                f"- Как запомнить: {item.get('memory', '')}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Готово: {csv_path}")
    print(f"Готово: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
