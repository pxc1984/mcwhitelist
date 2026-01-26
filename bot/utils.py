import re

from aiogram import types


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def format_user(user: types.User) -> str:
    if user.username:
        return f"@{user.username}"
    return f'<a href="tg://user?id={user.id}">{user.full_name}</a>'
