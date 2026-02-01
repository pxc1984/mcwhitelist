from dataclasses import dataclass
from typing import Dict


TextMap = Dict[str, str]


LOCALES: Dict[str, TextMap] = {
    "en": {
        "start": "Hi! I manage the Minecraft whitelist for this server.\n{hint}",
        "username_hint": "Send your Minecraft username to request access to the whitelist.\nUse the exact name you use in-game.",
        "request_sent": "Thanks! I sent your request (ID: {request_id}) to the admins.\nYou'll get a notification once it's reviewed.",
        "admin_request": (
            "New whitelist request #{request_id}\nTelegram: {mention} (ID: {tg_id})\nMinecraft username: {username}"
        ),
        "not_allowed": "You are not allowed to do that.",
        "request_not_found": "Request not found",
        "already_handled": "Already handled",
        "rcon_failed": "RCON failed, check logs.",
        "approved_user": "Good news! Your whitelist request #{request_id} was approved.",
        "denied_user": "Your whitelist request #{request_id} was denied.",
        "invalid_request": "Invalid request id",
        "approve_button": "Approve",
        "deny_button": "Deny",
        "invalid_username": "That doesn't look like a valid Minecraft username. Use 3-16 letters, numbers, or underscores.",
        "profile_button": "User profile",
        "ask_comment": "Do you have any additional comments to admins about your request?",
        "admin_comment": "Comment: {comment}",
        "no_comment": "No additional comments.",
        "skip_button": "Skip",
        "admin_verdict_approved": "Approved by {admin}",
        "admin_verdict_denied": "Denied by {admin}",
        "private_only": "This action is only available in a private chat.",
        "whitelist_cleanup_started": "Syncing whitelist...",
        "whitelist_cleanup_none": "Whitelist sync finished. Nothing to remove.",
        "whitelist_cleanup_done": "Whitelist sync finished. Removed {count} usernames.",
        "whitelist_cleanup_list": "Removed: {usernames}",
    },
    "ru": {
        "start": "Привет! Я помогаю управлять вайтлистом этого сервера.\n{hint}",
        "username_hint": "Отправь свой ник Minecraft, чтобы подать заявку на вайтлист.\nНик должен совпадать с игровым.\n\nЕсли ты не из ЦУ, в комментариях оставь тг ЦУ'шника, который мог бы за тебя ручиться🥸",
        "request_sent": "Спасибо! Я отправил твою заявку (ID: {request_id}) администраторам.\nПосле проверки тебя уведомят.",
        "admin_request": (
            "Новая заявка на вайтлист #{request_id}\nТелеграм: {mention} (ID: {tg_id})\nНик в Minecraft: {username}"
        ),
        "not_allowed": "У тебя нет прав на это действие.",
        "request_not_found": "Заявка не найдена",
        "already_handled": "Заявка уже обработана",
        "rcon_failed": "Не удалось выполнить команду RCON, см. логи.",
        "approved_user": "Отличные новости! Твоя заявка #{request_id} одобрена.",
        "denied_user": "Твоя заявка #{request_id} отклонена.",
        "invalid_request": "Некорректный ID заявки",
        "approve_button": "Одобрить",
        "deny_button": "Отклонить",
        "invalid_username": "Похоже, ник некорректен. Используй 3–16 символов: буквы, цифры или подчёркивания.",
        "profile_button": "Профиль в TG",
        "ask_comment": "Есть ли дополнительные комментарии для админов?",
        "admin_comment": "Комментарий: {comment}",
        "no_comment": "Без дополнительных комментариев.",
        "skip_button": "Пропустить",
        "admin_verdict_approved": "Одобрено: {admin}",
        "admin_verdict_denied": "Отклонено: {admin}",
        "private_only": "Это действие доступно только в личном чате.",
        "whitelist_cleanup_started": "Синхронизирую вайтлист...",
        "whitelist_cleanup_none": "Синхронизация завершена. Удалять нечего.",
        "whitelist_cleanup_done": "Синхронизация завершена. Удалено {count} ников.",
        "whitelist_cleanup_list": "Удалены: {usernames}",
    },
}


def get_text(locale: str, key: str) -> str:
    default = LOCALES.get("en", {})
    lang_map = LOCALES.get(locale, default)
    return lang_map.get(key, default.get(key, key))


@dataclass(frozen=True)
class Locale:
    name: str

    def t(self, key: str, **kwargs: str) -> str:
        return get_text(self.name, key).format(**kwargs)
