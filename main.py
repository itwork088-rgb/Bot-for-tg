import logging
import os
from urllib.parse import urlsplit

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MenuButtonWebApp,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger(__name__)


def validate_mini_app_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    url = value.strip()
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("MINI_APP_URL must be a public HTTPS URL.")
    return url


def validate_make_webhook_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None

    url = value.strip()
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or not parsed.hostname.startswith("hook.")
        or not parsed.hostname.endswith(".make.com")
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("MAKE_MESSAGE_WEBHOOK_URL must be a Make HTTPS webhook URL.")
    return url


def mini_app_keyboard(url: str | None) -> InlineKeyboardMarkup | None:
    if not url:
        return None
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📱 Открыть «Мои привычки»",
                    web_app=WebAppInfo(url=url),
                )
            ]
        ]
    )


async def configure_mini_app_menu(application: Application) -> None:
    mini_app_url: str | None = application.bot_data.get("mini_app_url")
    if mini_app_url:
        await application.bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Мои привычки",
                web_app=WebAppInfo(url=mini_app_url),
            )
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        mini_app_url: str | None = context.application.bot_data.get("mini_app_url")
        text = "Привет! Я AI-бот. Напиши мне сообщение, и я постараюсь помочь."
        if mini_app_url:
            text += "\n\nОткрой трекер привычек кнопкой ниже."
        else:
            text += (
                "\n\nТрекер привычек пока не подключён: добавь публичный HTTPS-адрес "
                "Mini App в MINI_APP_URL."
            )
        text += "\nКоманда /help покажет, что я умею."
        await update.message.reply_text(
            text,
            reply_markup=mini_app_keyboard(mini_app_url),
        )


async def track_incoming_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    message = update.message
    webhook_url: str | None = context.application.bot_data.get(
        "make_message_webhook_url"
    )
    if not webhook_url or not message:
        return

    text = message.text or message.caption
    if not text:
        return

    user = message.from_user
    payload = {
        "event": "telegram_message",
        "source": "telegram",
        "message_id": message.message_id,
        "chat_id": str(message.chat_id),
        "sender_id": str(user.id) if user else None,
        "username": user.username if user else None,
        "received_at": message.date.isoformat(),
        "text": text,
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        logger.error(
            "Make message logging failed with HTTP %s",
            error.response.status_code,
        )
    except httpx.RequestError as error:
        logger.error(
            "Make message logging request failed (%s)",
            type(error).__name__,
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        mini_app_url: str | None = context.application.bot_data.get("mini_app_url")
        app_help = (
            "Открой трекер привычек кнопкой «Мои привычки»."
            if mini_app_url
            else "Трекер привычек подключается через публичный HTTPS-адрес MINI_APP_URL."
        )
        await update.message.reply_text(
            "Просто отправь мне текст — я отвечу с помощью Gemini.\n"
            f"{app_help}\nДоступные команды: /start, /help.",
            reply_markup=mini_app_keyboard(mini_app_url),
        )


async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    client: genai.Client = context.application.bot_data["gemini_client"]
    model: str = context.application.bot_data["gemini_model"]

    await update.message.chat.send_action("typing")
    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=update.message.text,
            config=genai.types.GenerateContentConfig(
                system_instruction=(
                    "Ты полезный и доброжелательный AI-ассистент. "
                    "Отвечай на языке пользователя."
                )
            ),
        )
    except APIError:
        logger.exception("Gemini API request failed")
        await update.message.reply_text(
            "Не удалось получить ответ от AI-сервиса. Попробуй ещё раз позже."
        )
        return

    if not response.text:
        await update.message.reply_text(
            "AI-сервис вернул пустой ответ. Попробуй сформулировать вопрос иначе."
        )
        return

    text = response.text
    for offset in range(0, len(text), 4000):
        await update.message.reply_text(text[offset : offset + 4000])


async def handle_error(
    update: object, context: ContextTypes.DEFAULT_TYPE
) -> None:
    logger.error(
        "Telegram update failed",
        exc_info=(type(context.error), context.error, context.error.__traceback__)
        if context.error
        else None,
    )


def main() -> None:
    load_dotenv()
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    try:
        mini_app_url = validate_mini_app_url(os.getenv("MINI_APP_URL"))
        make_message_webhook_url = validate_make_webhook_url(
            os.getenv("MAKE_MESSAGE_WEBHOOK_URL")
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", telegram_token),
            ("GEMINI_API_KEY", gemini_api_key),
        )
        if not value
    ]
    if missing:
        raise SystemExit(
            f"Не заданы обязательные переменные: {', '.join(missing)}. "
            "Добавь их в файл .env."
        )

    application = (
        Application.builder()
        .token(telegram_token)
        .post_init(configure_mini_app_menu)
        .build()
    )
    application.bot_data["gemini_client"] = genai.Client(api_key=gemini_api_key)
    application.bot_data["gemini_model"] = gemini_model
    application.bot_data["mini_app_url"] = mini_app_url
    application.bot_data["make_message_webhook_url"] = make_message_webhook_url

    application.add_handler(
        MessageHandler(
            filters.TEXT | filters.CAPTION,
            track_incoming_message,
            block=False,
        ),
        group=-1,
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, answer)
    )
    application.add_error_handler(handle_error)

    logger.info("Starting Telegram bot with Gemini model %s", gemini_model)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        level=logging.INFO,
    )
    main()
