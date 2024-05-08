from app.core.clients.base_clients import ChatGenerationClient
from app.core.clients.openai import ChatGenerationOpenAIClient
from app.core.clients.dashscope import ChatGenerationDashscopeClient
from app.core.config import config


class ChatGenerationClientManager:

    @staticmethod
    def get_client(provider_name: str) -> ChatGenerationClient:
        if provider_name == "openai":
            return ChatGenerationOpenAIClient(
                api_key=config.openai_api_key,
                base_url=config.openai_base_url,
            )
        elif provider_name == "deepseek":
            return ChatGenerationOpenAIClient(
                api_key=config.deepseek_api_key,
                base_url=config.deepseek_base_url,
            )
        elif provider_name == "dashscope":
            return ChatGenerationDashscopeClient(
                api_key=config.dashscope_api_key,
                base_url=config.dashscope_base_url,
            )
        else:
            raise ValueError(f"No client found for provider {provider_name}")
