import logging

import pytest

from bot.config import parse_admin_ids
from bot.texts import Locale
from bot.utils import USERNAME_RE, format_user

from .fakes import FakeUser


def test_parse_admin_ids_skips_invalid(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.WARNING)
    ids = parse_admin_ids("1, 2, abc, 3")
    assert ids == [1, 2, 3]
    assert any("Skipped admin id" in record.message for record in caplog.records)


def test_locale_fallback_and_format() -> None:
    locale = Locale("en")
    assert "Hi!" in locale.t("start", hint="hint")
    assert locale.t("missing_key") == "missing_key"


def test_username_regex() -> None:
    assert USERNAME_RE.match("Player_01")
    assert USERNAME_RE.match("a3_")
    assert not USERNAME_RE.match("aa")
    assert not USERNAME_RE.match("bad-name")


def test_format_user_username() -> None:
    user = FakeUser(id=1, username="tester")
    assert format_user(user) == "@tester"


def test_format_user_link() -> None:
    user = FakeUser(id=2, full_name="User Two", username=None)
    assert "tg://user?id=2" in format_user(user)
