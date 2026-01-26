from pathlib import Path

import pytest

from bot.config import AppConfig, RconConfig
from bot.context import AppContext
from bot.services import whitelist as whitelist_service
from bot.texts import Locale

from .fakes import FakeBot, FakePool


@pytest.mark.asyncio
async def test_cleanup_secondary_accounts_keeps_primary(monkeypatch: pytest.MonkeyPatch) -> None:
    records = [
        {"id": 1, "user_id": 10, "username": "Primary"},
        {"id": 2, "user_id": 10, "username": "Alt"},
    ]
    removed: list[str] = []

    async def fake_fetch(pool, user_id):
        return records

    async def fake_delete(pool, request_id):
        removed.append(request_id)

    def fake_remove(config, username):
        removed.append(username)

    monkeypatch.setattr(whitelist_service, "fetch_approved_requests_by_user", fake_fetch)
    monkeypatch.setattr(whitelist_service, "delete_request", fake_delete)
    monkeypatch.setattr(whitelist_service, "remove_whitelist_player", fake_remove)

    context = AppContext(
        bot=FakeBot(),
        pool=FakePool(None),
        config=AppConfig(
            bot_token="token",
            admin_chat_id=1,
            admin_ids=[1],
            migrations_dir=Path("."),
            rcon=RconConfig("host", 1, "pass"),
            db_dsn="dsn",
            locale=Locale("en"),
        ),
    )

    removed_usernames = await whitelist_service.cleanup_secondary_accounts(
        context,
        user_id=10,
        keep_username="Primary",
    )

    assert removed_usernames == ["Alt"]
    assert "Alt" in removed
    assert 2 in removed


@pytest.mark.asyncio
async def test_sync_whitelist_removes_non_db(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_cleanup(context):
        return ["Alt"]

    async def fake_fetch_usernames(pool):
        return ["Primary"]

    def fake_list(config):
        return ["Primary", "Ghost"]

    removed: list[str] = []

    def fake_remove(config, username):
        removed.append(username)

    monkeypatch.setattr(whitelist_service, "cleanup_secondary_accounts", fake_cleanup)
    monkeypatch.setattr(whitelist_service, "fetch_approved_usernames", fake_fetch_usernames)
    monkeypatch.setattr(whitelist_service, "list_whitelisted_players", fake_list)
    monkeypatch.setattr(whitelist_service, "remove_whitelist_player", fake_remove)

    context = AppContext(
        bot=FakeBot(),
        pool=FakePool(None),
        config=AppConfig(
            bot_token="token",
            admin_chat_id=1,
            admin_ids=[1],
            migrations_dir=Path("."),
            rcon=RconConfig("host", 1, "pass"),
            db_dsn="dsn",
            locale=Locale("en"),
        ),
    )

    removed_usernames = await whitelist_service.sync_whitelist(context)

    assert removed_usernames == ["Alt", "Ghost"]
    assert removed == ["Ghost"]
