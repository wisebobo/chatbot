"""
LLM adapter layer
Provides a unified wrapper for calling the company AI platform and isolates underlying API differences.
Supports both streaming and standard output.
"""
import logging
from typing import AsyncIterator, List, Optional

import httpx
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMAdapter:
    """
    LLM adapter
    Wraps the company AI platform (OpenAI-compatible interface) into a LangChain callable object
    """

    def __init__(self):
        self._settings = get_settings().llm
        self._client: Optional[ChatOpenAI] = None

    @property
    def client(self) -> ChatOpenAI:
        """Lazily load the LLM client (singleton)"""
        if self._client is None:
            self._client = ChatOpenAI(
                base_url=self._settings.api_base_url,
                api_key=self._settings.api_key,
                model=self._settings.model_name,
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
                timeout=self._settings.request_timeout,
                max_retries=self._settings.max_retries,
            )
        return self._client

    async def ainvoke(self, messages: List[BaseMessage]) -> BaseMessage:
        """
        Asynchronously call the LLM and return the full response
        
        Args:
            messages: list of messages
            
        Returns:
            LLM response message
        """
        logger.debug(f"LLM invoke, message count: {len(messages)}")
        try:
            response = await self.client.ainvoke(messages)
            logger.debug(f"LLM response: {response.content[:100]}...")
            return response
        except httpx.TimeoutException as e:
            logger.error(f"LLM request timeout: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM invoke failed: {e}", exc_info=True)
            raise

    async def astream(self, messages: List[BaseMessage]) -> AsyncIterator[str]:
        """
        Asynchronously call the LLM in streaming mode
        
        Args:
            messages: list of messages
            
        Yields:
            individual text chunks
        """
        logger.debug(f"LLM stream invoke, message count: {len(messages)}")
        try:
            async for chunk in self.client.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LLM stream failed: {e}", exc_info=True)
            raise

    def get_tool_calling_client(self, tools: list) -> ChatOpenAI:
        """
        Get an LLM client bound with tools (for function calling)
        
        Args:
            tools: list of LangChain tools
            
        Returns:
            tool-enabled LLM client
        """
        return self.client.bind_tools(tools)


# global adapter singleton
_llm_adapter: Optional[LLMAdapter] = None


def get_llm_adapter() -> LLMAdapter:
    """Get the LLM adapter singleton"""
    global _llm_adapter
    if _llm_adapter is None:
        _llm_adapter = LLMAdapter()
    return _llm_adapter
