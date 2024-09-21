import atexit
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.tl.types import User, Channel


class GroupChatScrapper:
    def __init__(self, telegram_api_id, telegram_api_hash):
        self.client = TelegramClient("session", api_id=telegram_api_id, api_hash=telegram_api_hash)
        # Первый запуск клиента попросит нас залогиниться в Telegram аккаунт в терминале
        self.client.start()
        # telethon по умолчанию хранит данные сессии в БД на диске, поэтому работу с клиентом
        # нужно завершать корректно, чтобы не сломать БД
        atexit.register(self.client.disconnect)

    @staticmethod
    def get_telegram_user_name(sender):
        # Для выжимки нам нужны имена отправителей сообщений (позже увидим, зачем именно)
        if type(sender) is User:
            if sender.first_name and sender.last_name:
                return sender.first_name + " " + sender.last_name
            elif sender.first_name:
                return sender.first_name
            elif sender.last_name:
                return sender.last_name
            else:
                return "<unknown>"
        else:
            if type(sender) is Channel:
                return sender.title

    @staticmethod
    def get_datetime_from(lookback_period):
        return (datetime.utcnow() - timedelta(seconds=lookback_period)).replace(tzinfo=timezone.utc)

    def get_message_history(self, chat_id, lookback_period):
        history = []
        datetime_from = self.get_datetime_from(lookback_period)
        for message in self.client.iter_messages(chat_id):
            if message.date < datetime_from:
                break
            if not message.text:
                # Пропускаем не-текстовые сообщения
                continue
            sender = message.get_sender()
            data = {
                "id": message.id,
                "datetime": str(message.date),
                "text": message.text,
                "sender_user_name": self.get_telegram_user_name(sender),
                "sender_user_id": sender.id,
                "is_reply": message.is_reply
            }
            if message.is_reply:
                data["reply_to_message_id"] = message.reply_to.reply_to_msg_id
            history.append(data)
        return list(reversed(history))