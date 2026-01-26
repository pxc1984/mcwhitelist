import pytest

from bot import db

from .fakes import FakeConn, FakePool


@pytest.mark.asyncio
async def test_create_request() -> None:
    conn = FakeConn()
    conn.fetchrow_result = {"id": 42}
    pool = FakePool(conn)

    request_id = await db.create_request(pool, 1, 2, "Steve", "hello")

    assert request_id == 42
    assert "INSERT INTO whitelist_requests" in conn.last_query
    assert conn.last_params == (1, 2, "Steve", "hello")


@pytest.mark.asyncio
async def test_fetch_request() -> None:
    conn = FakeConn()
    conn.fetchrow_result = {"id": 7}
    pool = FakePool(conn)

    record = await db.fetch_request(pool, 7)

    assert record == {"id": 7}
    assert "SELECT * FROM whitelist_requests" in conn.last_query
    assert conn.last_params == (7,)


@pytest.mark.asyncio
async def test_fetch_user_by_mc_username() -> None:
    conn = FakeConn()
    conn.fetchrow_result = {"user_id": 99}
    pool = FakePool(conn)

    user_id = await db.fetch_user_by_mc_username(pool, "Steve")

    assert user_id == 99
    assert "WHERE username = $1" in conn.last_query
    assert conn.last_params == ("Steve",)


@pytest.mark.asyncio
async def test_fetch_user_by_mc_username_missing() -> None:
    conn = FakeConn()
    conn.fetchrow_result = None
    pool = FakePool(conn)

    user_id = await db.fetch_user_by_mc_username(pool, "Steve")

    assert user_id is None


@pytest.mark.asyncio
async def test_fetch_approved_usernames() -> None:
    conn = FakeConn()
    conn.fetch_result = [{"username": "Steve"}, {"username": "Alex"}]
    pool = FakePool(conn)

    names = await db.fetch_approved_usernames(pool)

    assert names == ["Steve", "Alex"]
    assert "status = 'approved'" in conn.last_query


@pytest.mark.asyncio
async def test_mark_request_status() -> None:
    conn = FakeConn()
    pool = FakePool(conn)

    await db.mark_request_status(pool, 5, "revoked", 10)

    assert conn.execute_calls
    query, params = conn.execute_calls[-1]
    assert "UPDATE whitelist_requests" in query
    assert params == (5, "revoked", 10)


@pytest.mark.asyncio
async def test_delete_request() -> None:
    conn = FakeConn()
    pool = FakePool(conn)

    await db.delete_request(pool, 11)

    query, params = conn.execute_calls[-1]
    assert "DELETE FROM whitelist_requests" in query
    assert params == (11,)
