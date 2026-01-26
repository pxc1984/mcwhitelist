import re

from aiogram import types


USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def format_user(user: types.User) -> str:
    label = f"@{user.username}" if user.username else user.full_name
    return f'<a href="tg://user?id={user.id}">{label}</a>'
