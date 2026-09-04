# Что добавлено для работы с Excel и данными

Сайт Namaskar остается простым PWA: он читает готовые файлы `data/asanas.json` и
`data/study.json`. Python добавлен как служебный слой, чтобы удобнее вести базу в
Excel и не править JSON руками.

## Источник данных

В проект добавлена папка `source/`:

- `asana_catalog_v1.xlsx` — главный каталог асан.
- `asana_catalog_v1.csv` — текстовая копия каталога.
- `asana_names_study.xlsx` — учебный файл по названиям асан.
- `asana_names_study.csv` — текстовая копия учебного файла.

## Инструменты

- `tools/generate_asanas.py` читает Excel/CSV и пересобирает данные для сайта:
  `data/asanas.json`, `data/study.json`, а также корневые копии `asanas.json`,
  `study.json`. Дополнительную локальную папку приложения можно указать отдельно.
- `tools/validate_data.py` проверяет качество базы: обязательные поля, картинки,
  длительности, дубли ID, соответствие учебных карточек каталогу.
- `tools/build_study_file.py` создает учебные материалы из `data/study.json`:
  `source/asana_names_study.generated.csv` и
  `source/asana_names_study.generated.md`.
- `tools/watch_excel.py` следит за файлами в `source/` и автоматически запускает
  пересборку после сохранения Excel/CSV.

## Как добиться обновления после Excel

Локально:

```powershell
cd D:\cline\namaskar-github-upload
python tools\watch_excel.py
```

Пока watcher открыт, можно менять `source\asana_catalog_v1.xlsx`. После сохранения
скрипт пересоберет JSON внутри этой же папки проекта, и локальный сайт увидит
изменения после обновления страницы.

Если локальное приложение лежит в другой папке, путь можно указать разово:

```powershell
python tools\watch_excel.py --local-app "C:\путь\к\namaskar\app"
```

Или создать личный файл `namaskar.local.json` рядом с `index.html`:

```json
{
  "local_app": "C:\\путь\\к\\namaskar\\app"
}
```

Этот файл добавлен в `.gitignore`, поэтому на каждом компьютере может быть свой
путь. Пример лежит в `namaskar.local.example.json`.

Предупреждения валидатора про одинаковые SVG-схемы не останавливают сборку. Это
контрольный список для дальнейшей ручной доработки картинок асан.

На публичном сайте:

```powershell
git add .
git commit -m "Update asana data"
git push origin main
```

После `git push` Vercel получает новую версию из GitHub и обновляет сайт.

## Почему Excel не может обновлять Vercel сам

Опубликованный сайт работает на сервере Vercel, а Excel лежит на локальном диске.
Браузер не имеет права читать этот файл напрямую. Поэтому нужен промежуточный шаг:
Excel -> Python-скрипт -> JSON -> GitHub -> Vercel.

Это бесплатно и не усложняет само приложение.

## Облачный вариант через GitHub

Если хочется работать без привязки к компьютеру, редактируйте CSV-файлы в GitHub:

- `source/asana_catalog_v1.csv`
- `source/asana_names_study.csv`

Workflow `.github/workflows/build-data.yml` сам пересоберет JSON, проверит данные
и закоммитит готовые файлы обратно в репозиторий. Подробная инструкция есть в
`GITHUB_WORKFLOW.md`.
