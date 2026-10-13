import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from telegram import InlineKeyboardMarkup, MenuButtonWebApp

from main import (
    configure_mini_app_menu,
    mini_app_keyboard,
    start,
    validate_mini_app_url,
)


class MiniAppConfigTests(unittest.TestCase):
    def test_accepts_public_https_url(self) -> None:
        self.assertEqual(
            validate_mini_app_url(" https://example.com/habits/ "),
            "https://example.com/habits/",
        )

    def test_allows_missing_url(self) -> None:
        self.assertIsNone(validate_mini_app_url(None))
        self.assertIsNone(validate_mini_app_url("  "))

    def test_rejects_non_https_or_credentials(self) -> None:
        for url in (
            "http://example.com",
            "https:///missing-host",
            "https://user:password@example.com",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_mini_app_url(url)

    def test_keyboard_only_exists_when_configured(self) -> None:
        self.assertIsNone(mini_app_keyboard(None))
        keyboard = mini_app_keyboard("https://example.com/habits/")
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        self.assertEqual(
            keyboard.inline_keyboard[0][0].web_app.url,
            "https://example.com/habits/",
        )


class MiniAppHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_start_includes_web_app_button(self) -> None:
        message = SimpleNamespace(reply_text=AsyncMock())
        context = SimpleNamespace(
            application=SimpleNamespace(
                bot_data={"mini_app_url": "https://example.com/habits/"}
            )
        )

        await start(SimpleNamespace(message=message), context)

        message.reply_text.assert_awaited_once()
        self.assertIsInstance(
            message.reply_text.await_args.kwargs["reply_markup"],
            InlineKeyboardMarkup,
        )

    async def test_menu_button_is_configured_when_url_exists(self) -> None:
        set_chat_menu_button = AsyncMock()
        application = SimpleNamespace(
            bot_data={"mini_app_url": "https://example.com/habits/"},
            bot=SimpleNamespace(set_chat_menu_button=set_chat_menu_button),
        )

        await configure_mini_app_menu(application)

        menu_button = set_chat_menu_button.await_args.kwargs["menu_button"]
        self.assertIsInstance(menu_button, MenuButtonWebApp)
        self.assertEqual(menu_button.web_app.url, "https://example.com/habits/")

    async def test_menu_button_is_not_configured_without_url(self) -> None:
        set_chat_menu_button = AsyncMock()
        application = SimpleNamespace(
            bot_data={"mini_app_url": None},
            bot=SimpleNamespace(set_chat_menu_button=set_chat_menu_button),
        )

        await configure_mini_app_menu(application)

        set_chat_menu_button.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
