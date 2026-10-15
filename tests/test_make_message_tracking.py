import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from main import track_incoming_message, validate_make_webhook_url


class MakeWebhookConfigTests(unittest.TestCase):
    def test_accepts_make_webhook_url(self) -> None:
        url = "https://hook.eu1.make.com/example-id"
        self.assertEqual(validate_make_webhook_url(url), url)

    def test_allows_missing_webhook_url(self) -> None:
        self.assertIsNone(validate_make_webhook_url(None))
        self.assertIsNone(validate_make_webhook_url(" "))

    def test_rejects_untrusted_webhook_urls(self) -> None:
        for url in (
            "http://hook.eu1.make.com/example",
            "https://make.com/example",
            "https://hook.eu1.make.com.attacker.invalid/example",
            "https://user:password@hook.eu1.make.com/example",
            "https://hook.eu1.make.com/example?token=secret",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_make_webhook_url(url)


class IncomingMessageTrackingTests(unittest.IsolatedAsyncioTestCase):
    async def test_forwards_text_and_minimal_message_metadata(self) -> None:
        message = SimpleNamespace(
            text="Hello",
            caption=None,
            message_id=7,
            chat_id=123,
            from_user=SimpleNamespace(id=456),
            date=datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc),
        )
        context = SimpleNamespace(
            application=SimpleNamespace(
                bot_data={
                    "make_message_webhook_url": (
                        "https://hook.eu1.make.com/example-id"
                    )
                }
            )
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = False
        client.post.return_value = SimpleNamespace(raise_for_status=Mock())

        with patch("main.httpx.AsyncClient", return_value=client):
            await track_incoming_message(
                SimpleNamespace(message=message), context
            )

        client.post.assert_awaited_once_with(
            "https://hook.eu1.make.com/example-id",
            json={
                "source": "telegram",
                "message_id": 7,
                "chat_id": "123",
                "sender_id": "456",
                "received_at": "2026-10-15T12:00:00+00:00",
                "text": "Hello",
            },
        )

    async def test_does_not_send_when_webhook_is_not_configured(self) -> None:
        context = SimpleNamespace(application=SimpleNamespace(bot_data={}))
        with patch("main.httpx.AsyncClient") as client:
            await track_incoming_message(
                SimpleNamespace(message=SimpleNamespace(text="Hello")),
                context,
            )
        client.assert_not_called()

    async def test_forwards_caption_when_message_has_no_text(self) -> None:
        message = SimpleNamespace(
            text=None,
            caption="Photo description",
            message_id=8,
            chat_id=123,
            from_user=SimpleNamespace(id=456),
            date=datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc),
        )
        context = SimpleNamespace(
            application=SimpleNamespace(
                bot_data={
                    "make_message_webhook_url": (
                        "https://hook.eu1.make.com/example-id"
                    )
                }
            )
        )
        client = AsyncMock()
        client.__aenter__.return_value = client
        client.__aexit__.return_value = False
        client.post.return_value = SimpleNamespace(raise_for_status=Mock())

        with patch("main.httpx.AsyncClient", return_value=client):
            await track_incoming_message(
                SimpleNamespace(message=message), context
            )

        self.assertEqual(
            client.post.await_args.kwargs["json"]["text"], "Photo description"
        )


if __name__ == "__main__":
    unittest.main()
