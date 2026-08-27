# Обновление Namaskar

Рабочая папка приложения: `D:\cline\namaskar\app`.

## Обычный цикл

```powershell
cd D:\cline\namaskar\app
git status
git add .
git commit -m "Update Namaskar"
git push
```

Vercel сам обновит опубликованное приложение после `git push`.

## Что коммитить

Коммитить нужно файлы приложения: `index.html`, `styles.css`, `app.js`, `data`, `icons`, `visuals`, `manifest.webmanifest`, `service-worker.js`, `vercel.json`.

Excel-файлы из `D:\cline\namaskar` можно хранить локально как мастер-базу и не публиковать, если не хотите выкладывать их в интернет.
