#!/usr/bin/env python3
"""Build Namaskar app data from the editable source spreadsheets.

The app itself stays static. This script turns the source Excel/CSV files into
JSON files that the PWA reads from data/asanas.json and data/study.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "namaskar.local.json"
DEFAULT_CATALOGS = (
    ROOT / "source" / "asana_catalog_v1.xlsx",
    ROOT / "source" / "asana_catalog_v1.csv",
)
DEFAULT_STUDY = (
    ROOT / "source" / "asana_names_study.xlsx",
    ROOT / "source" / "asana_names_study.csv",
)

CATALOG_HEADERS = {
    "ID": "id",
    "Раздел": "section",
    "Направления и эффект": "goals",
    "Уровень": "level",
    "Название асаны в оригинале": "sanskrit",
    "Транслитерация на русском": "transliteration",
    "Популярное название на русском": "ru",
    "Объяснение выполнения": "execution",
    "Минуты": "minutes",
    "Противопоказания и ограничения": "contraindications",
    "Текст для озвучивания": "voice",
    "Как встроить перед асаной": "transitionIn",
    "Как выйти или компенсировать": "transitionOut",
    "Картинка визуализация": "image",
    "Заметки": "notes",
}

STUDY_HEADERS = {
    "ID": "id",
    "Оригинальное название": "sanskrit",
    "Транслитерация на русском": "transliteration",
    "Популярное название": "ru",
    "По слогам для чтения": "syllables",
    "Разбор по частям": "parts",
    "Буквальный смысл": "literal",
    "От чего произошло": "origin",
    "Подсказка для запоминания": "memory",
    "Раздел": "section",
}


def first_existing(candidates: Iterable[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path
    listed = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(f"Не найден ни один источник:\n{listed}")


def column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    index = 0
    for char in letters:
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def rows_to_dicts(rows: list[list[str]]) -> list[dict[str, str]]:
    if not rows:
        return []
    headers = [value.strip() for value in rows[0]]
    records = []
    for row in rows[1:]:
        record = {}
        for index, header in enumerate(headers):
            record[header] = (row[index] if index < len(row) else "").strip()
        if any(record.values()):
            records.append(record)
    return records


def read_xlsx(path: Path) -> list[dict[str, str]]:
    """Read the first sheet from a simple .xlsx file using only stdlib."""
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", ns):
                text_parts = [node.text or "" for node in item.findall(".//main:t", ns)]
                shared_strings.append("".join(text_parts))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        first_sheet = workbook.find("main:sheets/main:sheet", ns)
        if first_sheet is None:
            raise ValueError(f"В файле {path} не найден первый лист")

        rel_id = first_sheet.attrib[f"{{{ns['rel']}}}id"]
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target = None
        for rel in rels.findall("pkgrel:Relationship", ns):
            if rel.attrib.get("Id") == rel_id:
                target = rel.attrib["Target"]
                break
        if target is None:
            raise ValueError(f"Не удалось найти лист {rel_id} в {path}")

        sheet_path = "xl/" + target.lstrip("/")
        sheet = ET.fromstring(archive.read(sheet_path))

    rows: list[list[str]] = []
    for row in sheet.findall(".//main:sheetData/main:row", ns):
        values: list[str] = []
        for cell in row.findall("main:c", ns):
            idx = column_index(cell.attrib.get("r", "A1"))
            while len(values) <= idx:
                values.append("")

            cell_type = cell.attrib.get("t")
            value_node = cell.find("main:v", ns)
            inline_node = cell.find("main:is/main:t", ns)
            raw = value_node.text if value_node is not None else ""
            if cell_type == "s" and raw:
                values[idx] = shared_strings[int(raw)]
            elif cell_type == "inlineStr" and inline_node is not None:
                values[idx] = inline_node.text or ""
            else:
                values[idx] = raw or ""
        rows.append(values)

    return rows_to_dicts(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_table(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".xlsx":
        return read_xlsx(path)
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    raise ValueError(f"Неподдерживаемый формат: {path.suffix}")


def normalize_minutes(value: str) -> int | float | str:
    value = (value or "").strip().replace(",", ".")
    if not value:
        return ""
    try:
        number = float(value)
    except ValueError:
        return value
    return int(number) if number.is_integer() else number


def map_record(record: dict[str, str], mapping: dict[str, str]) -> dict[str, object]:
    item: dict[str, object] = {}
    for source, target in mapping.items():
        value = record.get(source, "").strip()
        item[target] = normalize_minutes(value) if target == "minutes" else value
    return item


def write_json(path: Path, data: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def read_local_app(cli_path: Path | None, disabled: bool) -> Path | None:
    if disabled:
        return None
    if cli_path:
        return cli_path.expanduser().resolve()
    if LOCAL_CONFIG.exists():
        config = json.loads(LOCAL_CONFIG.read_text(encoding="utf-8"))
        value = str(config.get("local_app", "")).strip()
        if value:
            return Path(value).expanduser().resolve()
    return None


def sync_local_app(local_app: Path | None) -> None:
    if local_app is None:
        return
    if not local_app.exists():
        print(f"Локальная папка приложения не найдена, копирование пропущено: {local_app}")
        return
    target = local_app / "data"
    target.mkdir(parents=True, exist_ok=True)
    for name in ("asanas.json", "study.json"):
        source = ROOT / "data" / name
        if source.exists():
            shutil.copy2(source, target / name)
    print(f"Синхронизировано с локальным приложением: {target}")


def build(catalog_path: Path, study_path: Path | None, mirror_root: bool, local_app: Path | None) -> None:
    asanas = [map_record(row, CATALOG_HEADERS) for row in read_table(catalog_path)]
    write_json(ROOT / "data" / "asanas.json", asanas)
    if mirror_root:
        write_json(ROOT / "asanas.json", asanas)

    study_count = 0
    if study_path and study_path.exists():
        study = [map_record(row, STUDY_HEADERS) for row in read_table(study_path)]
        write_json(ROOT / "data" / "study.json", study)
        if mirror_root:
            write_json(ROOT / "study.json", study)
        study_count = len(study)

    print(f"Готово: {len(asanas)} асан -> data/asanas.json")
    if study_count:
        print(f"Готово: {study_count} учебных карточек -> data/study.json")
    sync_local_app(local_app)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Собрать JSON для сайта Namaskar из Excel/CSV.")
    parser.add_argument("--catalog", type=Path, default=None, help="Путь к asana_catalog_v1.xlsx или .csv")
    parser.add_argument("--study", type=Path, default=None, help="Путь к asana_names_study.xlsx или .csv")
    parser.add_argument("--no-root-mirror", action="store_true", help="Не обновлять копии asanas.json/study.json в корне")
    parser.add_argument("--local-app", type=Path, default=None, help="Дополнительная локальная папка приложения")
    parser.add_argument("--no-local-sync", action="store_true", help="Не копировать JSON в локальную папку приложения")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        catalog = args.catalog or first_existing(DEFAULT_CATALOGS)
        study = args.study or first_existing(DEFAULT_STUDY)
        local_app = read_local_app(args.local_app, disabled=args.no_local_sync)
        build(catalog, study, mirror_root=not args.no_root_mirror, local_app=local_app)
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
