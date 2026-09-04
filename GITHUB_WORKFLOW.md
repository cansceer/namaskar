# Работа без привязки к компьютеру

Теперь можно менять базу асан через GitHub, без локальной разработки.

## Главная идея

Для работы прямо в GitHub главным редактируемым источником становятся CSV-файлы:

- `source/asana_catalog_v1.csv` — каталог асан для сайта.
- `source/asana_names_study.csv` — учебные карточки названий.

Когда эти файлы меняются в ветке `main`, GitHub Actions запускает Python-скрипты:

1. `tools/generate_asanas.py` пересобирает JSON для сайта.
2. `tools/validate_data.py` проверяет базу.
3. `tools/build_study_file.py` обновляет учебный экспорт.
4. GitHub сам делает коммит `Build Namaskar data` с готовыми файлами.
5. Vercel видит новый коммит и обновляет опубликованное приложение.

## Как редактировать через GitHub

1. Открыть репозиторий `cansceer/namaskar`.
2. Открыть `source/asana_catalog_v1.csv`.
3. Нажать карандаш `Edit this file`.
4. Внести правки.
5. Нажать `Commit changes`.

После этого открыть вкладку `Actions` и дождаться зеленой галочки у workflow
`Build Namaskar data`.

## Через редактор GitHub

На странице репозитория можно нажать клавишу `.`. Откроется браузерный редактор,
похожий на VS Code. В нем удобнее править большие CSV-файлы.

После правок нужно открыть Source Control слева, написать короткое сообщение
коммита и нажать `Commit & Push`.

## Когда использовать Excel

Excel по-прежнему можно использовать локально. Но если работа идет полностью через
GitHub, удобнее править CSV, потому что GitHub не редактирует XLSX как таблицу.

Если ты меняешь XLSX локально, потом нужно запустить:

```powershell
python tools\generate_asanas.py
python tools\validate_data.py
git add .
git commit -m "Update asana data"
git push origin main
```

## Что делать, если Actions не коммитит файлы

В GitHub нужно проверить настройку:

`Settings -> Actions -> General -> Workflow permissions`

Должно быть включено:

`Read and write permissions`

И желательно включить:

`Allow GitHub Actions to create and approve pull requests`

Для нашего workflow обычно достаточно `Read and write permissions`.

## Важный нюанс

Автоматический workflow читает именно CSV:

```text
source/asana_catalog_v1.csv
source/asana_names_study.csv
```

Так мы получаем независимость от конкретного компьютера и от установленного Excel.
