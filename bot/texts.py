from dataclasses import dataclass
from typing import Dict


TextMap = Dict[str, str]


LOCALES: Dict[str, TextMap] = {
    "en": {
        "start": "Hi! I manage the Minecraft whitelist for this server.\n{hint}",
        "username_hint": "Send your Minecraft username to request access to the whitelist.\nUse the exact name you use in-game.",
        "request_sent": "Thanks! I sent your request (ID: {request_id}) to the admins.\nYou'll get a notification once it's reviewed.",
        "admin_request": (
            "New whitelist request #{request_id}\n"
            "Telegram: {full_name} (ID: {tg_id})\n"
            "Minecraft username: {username}"
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
    },
    "ru": {
        "start": "Привет! Я помогаю управлять вайтлистом этого сервера.\n{hint}",
        "username_hint": "Отправь свой ник Minecraft, чтобы подать заявку на вайтлист.\nНик должен совпадать с игровым.",
        "request_sent": "Спасибо! Я отправил твою заявку (ID: {request_id}) администраторам.\nПосле проверки тебя уведомят.",
        "admin_request": (
            "Новая заявка на вайтлист #{request_id}\n"
            "Телеграм: {full_name} (ID: {tg_id})\n"
            "Ник в Minecraft: {username}"
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
