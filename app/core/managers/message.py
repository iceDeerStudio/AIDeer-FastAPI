from app.models.message import Message, Messages
from app.core.connections.redis import redis_client
from uuid import UUID


class MessageStorage:

    @staticmethod
    def uuid_to_str_wapper(func):
        def wrapper(*args, **kwargs):
            args_list = list(args)
            for i, arg in enumerate(args_list):
                if isinstance(arg, UUID):
                    args_list[i] = str(arg)
            for key, value in kwargs.items():
                if isinstance(value, UUID):
                    kwargs[key] = str(value)
            return func(*args_list, **kwargs)

        return wrapper

    @staticmethod
    @uuid_to_str_wapper
    def get_messages(chat_id: str | UUID) -> list[Message]:
        messages_str = redis_client.hget(f"messages", chat_id)
        if messages_str:
            return Messages.model_validate_json(messages_str).root
        raise ValueError("Chat Messages not found")

    @staticmethod
    @uuid_to_str_wapper
    def set_messages(chat_id: str | UUID, messages: list[Message]) -> None:
        messages_str = Messages.model_validate(messages).model_dump_json()
        redis_client.hset(f"messages", chat_id, messages_str)
        return None

    @staticmethod
    @uuid_to_str_wapper
    def add_message(chat_id: str | UUID, message: Message) -> None:
        messages = MessageStorage.get_messages(chat_id)
        messages.append(message)
        MessageStorage.set_messages(chat_id, messages)
        return None

    @staticmethod
    @uuid_to_str_wapper
    def copy_messages(from_chat_id: str | UUID, to_chat_id: str | UUID) -> None:
        message_str = redis_client.hget(f"messages", from_chat_id)
        if message_str:
            redis_client.hset(f"messages", to_chat_id, message_str)
        return None

    @staticmethod
    @uuid_to_str_wapper
    def delete_messages(chat_id: str | UUID) -> None:
        redis_client.hdel(f"messages", chat_id)
        return None
