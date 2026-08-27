# Публикация Namaskar через GitHub + Vercel

## Что требуется от вас один раз

1. Аккаунт GitHub: https://github.com
2. Аккаунт Vercel: https://vercel.com
3. Пустой GitHub-репозиторий, например `namaskar`.

## Шаг 1. Создать репозиторий на GitHub

1. Откройте GitHub.
2. Нажмите `+` -> `New repository`.
3. Repository name: `namaskar`.
4. Можно выбрать `Public` или `Private`.
   - Для GitHub Pages на бесплатном плане проще `Public`.
   - Для Vercel Hobby личный private-репозиторий тоже можно подключать, если он принадлежит вашему личному GitHub-аккаунту.
5. Не добавляйте README, .gitignore или license, потому что локальный коммит уже создан.
6. Нажмите `Create repository`.
7. Скопируйте HTTPS URL репозитория, например:
   `https://github.com/cansceer/namaskar.git`

## Шаг 2. Подключить локальную папку к GitHub

Выполнить в PowerShell:

```powershell
cd D:\cline\namaskar\app
git remote add origin https://github.com/cansceer/namaskar.git
git push -u origin main
```

Если Git попросит войти в GitHub, выполните вход в открывшемся окне.

## Шаг 3. Подключить Vercel

1. Откройте https://vercel.com
2. Войдите через GitHub.
3. Нажмите `Add New...` -> `Project`.
4. Выберите репозиторий `namaskar`.
5. Настройки проекта:
   - Framework Preset: `Other` или `No Framework`.
   - Root Directory: оставить по умолчанию, если в репозиторий отправлена именно папка `D:\cline\namaskar\app`.
   - Build Command: пусто.
   - Output Directory: пусто или `.`.
   - Install Command: пусто.
6. Нажмите `Deploy`.

После деплоя Vercel даст ссылку вида:
`https://namaskar-....vercel.app`

## Как обновлять приложение после локальных изменений

Каждый раз после изменений:

```powershell
cd D:\cline\namaskar\app
git status
git add .
git commit -m "Update Namaskar"
git push
```

После `git push` Vercel автоматически опубликует новую версию.

## Почему на GitHub Pages была ошибка JSON

Ошибка вида:
`Unexpected token '<', "<!DOCTYPE ..." is not valid JSON`

означает, что приложение запросило файл `data/asanas.json`, но вместо JSON получило HTML-страницу. Обычно это случается по одной из причин:

1. Папка `data` не была загружена в репозиторий.
2. Файлы лежат внутри папки `app`, а GitHub Pages публикует корень репозитория.
3. GitHub Pages еще не успел обновиться.

Проверка:
`https://cansceer.github.io/namaskar/data/asanas.json`

Если все хорошо, по этой ссылке должен открываться JSON, начинающийся с `[`.
Если открывается HTML или 404, значит папка `data` лежит не рядом с `index.html` на опубликованном сайте.
