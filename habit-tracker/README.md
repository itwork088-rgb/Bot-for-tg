# Habit Tracker — Telegram Mini App

Production: <https://habit-tracker-mini-app-eh4.pages.dev/>

## Структура проекта

```text
habit-tracker/
├── index.html
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── README.md
├── PLAN.md
├── TASK.md
└── src/
    ├── App.tsx
    ├── main.tsx
    └── styles.css
```

## Запуск

Нужен Node.js 20.19+ или 22.12+.

В PowerShell:

```powershell
cd "C:\Users\Student\Desktop\Bot for tg\habit-tracker"
npm install
npm run dev
```

Открой адрес Vite, показанный в терминале. Для production-сборки выполни
`npm run build`, а для локального просмотра готовой сборки — `npm run preview`.

## Использование в Telegram

Для локальной разработки можно открыть страницу в обычном браузере. Чтобы
запустить приложение внутри Telegram, разверни production-сборку на доступном
по HTTPS хостинге и укажи её адрес как Web App URL бота через BotFather.
Frontend использует только Telegram Web Apps SDK и не содержит bot token.

Чтобы открыть Mini App кнопкой существующего бота, укажи его публичный HTTPS
адрес в `MINI_APP_URL` в корневом `.env` и перезапусти бота. Бот добавит кнопку
в ответ `/start` и меню приложения. Для временной разработки можно открыть
публичный туннель к Vite командой `ngrok http --host-header=rewrite 5173`,
указать выданный HTTPS URL как `MINI_APP_URL` и держать оба процесса запущенными.
Подробные шаги размещения описаны в корневом `README.md`.

Привычки и отметки хранятся локально в браузере устройства. Они не
синхронизируются между устройствами и очищаются, если стереть данные сайта.

## Проверки

```powershell
npm run build
```

Ручной чек-лист находится в `TASK.md`.
