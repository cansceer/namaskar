#!/usr/bin/env python3
"""Validate Namaskar data files and local visual assets."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from hashlib import sha256
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASANA_FIELDS = (
    "id",
    "section",
    "goals",
    "level",
    "sanskrit",
    "transliteration",
    "ru",
    "execution",
    "minutes",
    "contraindications",
    "voice",
    "transitionIn",
    "transitionOut",
    "image",
)
REQUIRED_STUDY_FIELDS = (
    "id",
    "sanskrit",
    "transliteration",
    "ru",
    "syllables",
    "parts",
    "literal",
    "origin",
    "memory",
    "section",
)


def load_json(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError(f"{path} должен быть списком")
    return data


def is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def visual_signature(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r'aria-label="[^"]*"', 'aria-label=""', text)
    text = re.sub(r"\s+", " ", text).strip()
    return sha256(text.encode("utf-8")).hexdigest()


def validate_asanas(asanas: list[dict[str, object]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = [str(item.get("id", "")).strip() for item in asanas]

    for duplicated, count in Counter(ids).items():
        if duplicated and count > 1:
            errors.append(f"Дублируется ID асаны: {duplicated} ({count} раза)")

    visual_hashes: dict[str, list[str]] = {}
    for index, item in enumerate(asanas, start=1):
        item_id = str(item.get("id", f"строка {index}")).strip()
        for field in REQUIRED_ASANA_FIELDS:
            if is_blank(item.get(field)):
                errors.append(f"{item_id}: пустое поле {field}")

        minutes = item.get("minutes")
        if not isinstance(minutes, (int, float)) or minutes <= 0:
            errors.append(f"{item_id}: minutes должен быть положительным числом")

        image = str(item.get("image", "")).strip()
        image_path = ROOT / image
        if image and not image_path.exists():
            errors.append(f"{item_id}: не найден файл картинки {image}")
        elif image_path.exists() and image_path.suffix.lower() == ".svg":
            svg = image_path.read_text(encoding="utf-8", errors="ignore")
            if "<text" in svg:
                errors.append(f"{item_id}: внутри SVG остался видимый текст")
            visual_hashes.setdefault(visual_signature(image_path), []).append(item_id)

    for group in visual_hashes.values():
        if len(group) > 1:
            warnings.append(f"Одинаковая SVG-схема у асан: {', '.join(group)}")

    return errors, warnings


def validate_study(study: list[dict[str, object]], asana_ids: set[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    study_ids = {str(item.get("id", "")).strip() for item in study}

    missing_in_study = sorted(asana_ids - study_ids)
    if missing_in_study:
        warnings.append("Нет учебных карточек для: " + ", ".join(missing_in_study))

    for index, item in enumerate(study, start=1):
        item_id = str(item.get("id", f"строка {index}")).strip()
        if item_id and item_id not in asana_ids:
            warnings.append(f"{item_id}: учебная карточка есть, но такой асаны нет в каталоге")
        for field in REQUIRED_STUDY_FIELDS:
            if is_blank(item.get(field)):
                errors.append(f"{item_id}: пустое учебное поле {field}")

    return errors, warnings


def main() -> int:
    try:
        asanas = load_json(ROOT / "data" / "asanas.json")
        study = load_json(ROOT / "data" / "study.json")
    except Exception as error:
        print(f"Ошибка чтения JSON: {error}", file=sys.stderr)
        return 1

    errors, warnings = validate_asanas(asanas)
    study_errors, study_warnings = validate_study(study, {str(item.get("id", "")).strip() for item in asanas})
    errors.extend(study_errors)
    warnings.extend(study_warnings)

    print(f"Проверено асан: {len(asanas)}")
    print(f"Проверено учебных карточек: {len(study)}")
    print(f"Ошибок: {len(errors)}")
    print(f"Предупреждений: {len(warnings)}")

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
