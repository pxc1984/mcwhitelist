from typing import List

import pytest

from bot import rcon


class FakeClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.commands: List[str] = []

    def command(self, cmd: str) -> str:
        self.commands.append(cmd)
        return self.response


class FakeMCRcon:
    def __init__(self, response: str) -> None:
        self.client = FakeClient(response)

    def __enter__(self) -> FakeClient:
        return self.client

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_list_whitelisted_players_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_mcrcon(*args, **kwargs):
        return FakeMCRcon("There are 2 whitelisted players: Steve, Alex")

    monkeypatch.setattr(rcon, "MCRcon", fake_mcrcon)

    names = rcon.list_whitelisted_players(rcon.RconConfig("host", 1, "pass"))

    assert names == ["Steve", "Alex"]


def test_list_whitelisted_players_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_mcrcon(*args, **kwargs):
        return FakeMCRcon("No whitelist")

    monkeypatch.setattr(rcon, "MCRcon", fake_mcrcon)

    names = rcon.list_whitelisted_players(rcon.RconConfig("host", 1, "pass"))

    assert names == []
