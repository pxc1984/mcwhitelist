from pathlib import Path

import pytest
from aiogram.types import ReactionTypeEmoji

from bot.config import AppConfig, RconConfig
from bot.context import AppContext
from bot.handlers.comment import handle_comment
from bot.handlers.decision import handle_decision
from bot.handlers.skip_comment import skip_comment
from bot.handlers.start import handle_start
from bot.handlers.username import handle_username
from bot.handlers.whitelist_sync import handle_whitelist_sync
from bot.handlers.whois import handle_whois
from bot.texts import Locale

from .fakes import (
    FakeBot,
    FakeCallbackQuery,
    FakeChat,
    FakeFSMContext,
    FakeMessage,
    FakePool,
    FakeUser,
)


def build_context(admin_ids=None) -> AppContext:
    bot = FakeBot()
    pool = FakePool(None)
    config = AppConfig(
        bot_token="token",
        admin_chat_id=999,
        admin_ids=admin_ids or [1],
        migrations_dir=Path("."),
        rcon=RconConfig("host", 1, "pass"),
        db_dsn="dsn",
        locale=Locale("en"),
    )
    return AppContext(bot=bot, pool=pool, config=config)


@pytest.mark.asyncio
async def test_start_handler() -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1))

    await handle_start(message, context)

    assert message.answers
    assert "Hi!" in message.answers[0]


@pytest.mark.asyncio
async def test_username_handler_invalid() -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="bad-name")
    state = FakeFSMContext()

    await handle_username(message, state, context)

    assert message.answers == [context.config.locale.t("invalid_username")]


@pytest.mark.asyncio
async def test_username_handler_valid() -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="Steve")
    state = FakeFSMContext()

    await handle_username(message, state, context)

    assert state.data["username"] == "Steve"
    assert state.state is not None
    assert message.answers


@pytest.mark.asyncio
async def test_comment_handler_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="skip")
    state = FakeFSMContext()
    called = {}

    async def fake_finalize(msg, st, comment, ctx):
        called["comment"] = comment

    monkeypatch.setattr("bot.handlers.comment.finalize_request", fake_finalize)

    await handle_comment(message, state, context)

    assert called["comment"] is None


@pytest.mark.asyncio
async def test_skip_comment_private_only() -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(10), from_user=FakeUser(20))
    callback = FakeCallbackQuery(data="skip_comment", from_user=FakeUser(20), message=message)
    state = FakeFSMContext()

    await skip_comment(callback, state, context)

    assert callback.answers
    assert callback.answers[0]["show_alert"] is True


@pytest.mark.asyncio
async def test_decision_non_admin() -> None:
    context = build_context(admin_ids=[99])
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="req")
    callback = FakeCallbackQuery(data="approve:1", from_user=FakeUser(1), message=message)

    await handle_decision(callback, context)

    assert callback.answers
    assert callback.answers[0]["text"] == context.config.locale.t("not_allowed")


@pytest.mark.asyncio
async def test_decision_approve_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    context = build_context(admin_ids=[1])
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="req")
    callback = FakeCallbackQuery(data="approve:1", from_user=FakeUser(1), message=message)

    async def fake_fetch(pool, request_id):
        return {"id": 1, "user_id": 5, "username": "Steve", "status": "pending", "chat_id": 55}

    async def fake_mark(pool, request_id, status, decided_by):
        assert status == "approved"

    async def fake_cleanup(context, user_id=None, keep_username=None):
        assert user_id == 5
        assert keep_username == "Steve"
        return []

    def fake_whitelist(config, username):
        assert username == "Steve"

    monkeypatch.setattr("bot.handlers.decision.fetch_request", fake_fetch)
    monkeypatch.setattr("bot.handlers.decision.mark_request", fake_mark)
    monkeypatch.setattr("bot.handlers.decision.cleanup_secondary_accounts", fake_cleanup)
    monkeypatch.setattr("bot.handlers.decision.whitelist_player", fake_whitelist)

    await handle_decision(callback, context)

    assert callback.answers
    assert callback.answers[-1]["text"] == "Approved"
    assert context.bot.sent


@pytest.mark.asyncio
async def test_whitelist_sync_non_admin() -> None:
    context = build_context(admin_ids=[2])
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="/whitelist")

    await handle_whitelist_sync(message, context)

    assert message.replies == [context.config.locale.t("not_allowed")]


@pytest.mark.asyncio
async def test_whitelist_sync_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    context = build_context(admin_ids=[1])
    message = FakeMessage(chat=FakeChat(1), from_user=FakeUser(1), text="/whitelist")

    async def fake_sync(ctx):
        return ["Ghost"]

    monkeypatch.setattr("bot.handlers.whitelist_sync.sync_whitelist", fake_sync)

    await handle_whitelist_sync(message, context)

    assert context.config.locale.t("whitelist_cleanup_started") in message.replies[0]
    assert context.config.locale.t("whitelist_cleanup_done", count=1) in message.replies[1]


@pytest.mark.asyncio
async def test_whois_by_mc_username(monkeypatch: pytest.MonkeyPatch) -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1, "group"), from_user=FakeUser(1), text="/whois Steve")

    async def fake_fetch(pool, username):
        return 123

    monkeypatch.setattr("bot.handlers.whois.fetch_user_by_mc_username", fake_fetch)

    await handle_whois(message, context)

    assert message.replies
    assert "tg://user?id=123" in message.replies[0]


@pytest.mark.asyncio
async def test_whois_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1, "group"), from_user=FakeUser(1), text="/whois Steve")

    async def fake_fetch(pool, username):
        return None

    monkeypatch.setattr("bot.handlers.whois.fetch_user_by_mc_username", fake_fetch)

    await handle_whois(message, context)

    assert message.replies
    assert "Игрок" in message.replies[0]


@pytest.mark.asyncio
async def test_whois_no_args_reacts() -> None:
    context = build_context()
    message = FakeMessage(chat=FakeChat(1, "group"), from_user=FakeUser(1), text="/whois", message_id=42)

    await handle_whois(message, context)

    assert context.bot.reactions
    assert context.bot.reactions[0]["chat_id"] == 1
    assert context.bot.reactions[0]["message_id"] == 42
    reaction = context.bot.reactions[0]["reaction"]
    assert isinstance(reaction, list)
    assert isinstance(reaction[0], ReactionTypeEmoji)
    assert reaction[0].emoji == "🤡"
