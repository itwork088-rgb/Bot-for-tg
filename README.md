# Telegram AI bot

Бот отвечает на текстовые сообщения с помощью Gemini. Токены и ключи хранятся
локально в `.env` и не должны добавляться в Git.

## Запуск в Windows

Открой PowerShell в папке проекта и выполни:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe .\main.py
```

## Make.com MCP в VS Code

В `.vscode/mcp.json` настроен документированный Make MCP token endpoint
`https://eu1.make.com/mcp`. VS Code запросит Make MCP token при первом запуске.
Вставь именно Make MCP token (не Telegram bot token и не Gemini API key); поле
ввода скрывает значение, а VS Code хранит его в Secret Storage. В проекте
сохраняется только ссылка `${input:make-mcp-token}`. OAuth Client ID для этого
варианта не нужен.

Если токена ещё нет, создай его в Make: профиль → **API access** → **Tokens** →
**Add token**. Выдай `mcp:use` и только необходимые сценарные scopes, затем
скопируй токен в защищённое поле VS Code. Не вставляй токен в `.env`,
`.vscode/mcp.json` или чат.

В VS Code выполни **MCP: List Servers**, выбери `make` → **Stop Server**, затем
**Start Server** и на запрос вставь Make MCP token. После запуска инструменты
Make будут доступны в Copilot Chat.

Доступные инструменты зависят от выбранных разрешений Make. Разрешение на
запуск сценариев позволяет запускать активные сценарии организации, поэтому
выдавай его только если действительно нужно вызывать сценарии из Copilot.

Если виртуального окружения `venv` нет, создай его и установи зависимости:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

В `.env` должны быть заданы `TELEGRAM_BOT_TOKEN` (токен, полученный у
[@BotFather](https://t.me/BotFather)) и `GEMINI_API_KEY` (ключ Gemini API).
Опционально можно указать `GEMINI_MODEL`; по умолчанию используется
`gemini-2.5-flash`.

## Трекер привычек в Telegram

Mini App находится в папке `habit-tracker` и уже опубликовано на Cloudflare
Pages:

<https://habit-tracker-mini-app-eh4.pages.dev/>

HTTPS-адрес уже записан как `MINI_APP_URL` в локальном `.env`. При запуске
бота он добавит кнопку в `/start` и пункт в меню Telegram.

**Перед запуском:** токен бота был отправлен в чат, поэтому сначала отзови
его командой `/revoke` у [@BotFather](https://t.me/BotFather) и замени
`TELEGRAM_BOT_TOKEN` в локальном `.env`. Не отправляй новый токен в чат.
Затем запусти бота:

```powershell
.\venv\Scripts\python.exe .\main.py
```

Отправь боту `/start` и нажми «Открыть „Мои привычки“».

Чтобы опубликовать последующие изменения, собери приложение и отправь сборку
в уже созданный Pages-проект:

```powershell
Set-Location .\habit-tracker
npm run build
npm exec --yes --package=wrangler -- wrangler pages deploy .\dist --project-name habit-tracker-mini-app
```

Отправь боту обычный текст для ответа Gemini. Для остановки нажми `Ctrl+C`
в окне PowerShell.

## Журнал входящих сообщений в Make

Сценарий `Log Telegram incoming messages` принимает сообщения через Make
custom webhook. В корневом `.env` задай `MAKE_MESSAGE_WEBHOOK_URL` адресом
созданного webhook, затем перезапусти Python-бота. В Make передаются текст или
подпись сообщения, ID чата, ID отправителя и время; события сохраняются в
истории запусков сценария. Telegram polling остаётся включённым, поэтому
сценарий не устанавливает Telegram webhook и не мешает работе бота.

URL webhook содержит секретный идентификатор: храни его только в локальном
`.env`, не коммить и не отправляй в чат. Если адрес webhook раскрыт, удали его
и создай новый в Make.
