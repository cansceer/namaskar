# Python-инструменты Namaskar

Эта папка нужна не для работы сайта в браузере, а для подготовки данных.
Само приложение остается статическим PWA: HTML, CSS, JavaScript, JSON и SVG.

## Что здесь есть

- `generate_asanas.py` — пересобирает `data/asanas.json` и `data/study.json` из файлов `source/*.xlsx` или `source/*.csv`.
- `validate_data.py` — проверяет, что в базе есть обязательные поля, картинки существуют, ID не дублируются, а в SVG нет видимого текста.
- `build_study_file.py` — создает удобные учебные файлы по названиям асан из `data/study.json`.
- `watch_excel.py` — следит за изменениями в Excel/CSV и автоматически запускает сборку JSON.

## Как пользоваться

Из папки проекта:

```powershell
cd D:\cline\namaskar-github-upload
python tools\generate_asanas.py
python tools\validate_data.py
```

Для режима “сохранила Excel — сайт локально обновился”:

```powershell
python tools\watch_excel.py
```

После этого можно редактировать `source\asana_catalog_v1.xlsx`.
Когда файл сохранен, watcher пересоберет JSON внутри текущей папки проекта.
На локальном сайте достаточно обновить страницу.

Если приложение дополнительно лежит в другой локальной папке, можно указать ее:

```powershell
python tools\watch_excel.py --local-app "C:\путь\к\namaskar\app"
```

Чтобы не писать путь каждый раз, создайте рядом с `index.html` файл
`namaskar.local.json`:

```json
{
  "local_app": "C:\\путь\\к\\namaskar\\app"
}
```

Этот файл личный и не отправляется в GitHub. Пример формата есть в
`namaskar.local.example.json`.

Если валидатор показывает предупреждения про одинаковые SVG-схемы, это не ломает
сайт. Это список картинок, которые еще стоит перерисовать точнее.

## Важное про Vercel

Vercel не видит файлы на локальном диске. Чтобы изменения попали на публичный сайт,
после пересборки JSON нужно сделать обычный цикл:

```powershell
git add .
git commit -m "Update asana data"
git push origin main
```

После `git push` Vercel сам сделает новый деплой.
