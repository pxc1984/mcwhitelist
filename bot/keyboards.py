from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.texts import Locale


def build_admin_keyboard(request_id: int, locale: Locale, user_id: int) -> InlineKeyboardMarkup:
    approve = InlineKeyboardButton(text=locale.t("approve_button"), callback_data=f"approve:{request_id}")
    deny = InlineKeyboardButton(text=locale.t("deny_button"), callback_data=f"deny:{request_id}")
    profile = InlineKeyboardButton(text=locale.t("profile_button"), url=f"tg://user?id={user_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[approve, deny], [profile]])


def build_skip_keyboard(locale: Locale) -> InlineKeyboardMarkup:
    skip = InlineKeyboardButton(text=locale.t("skip_button"), callback_data="skip_comment")
    return InlineKeyboardMarkup(inline_keyboard=[[skip]])
