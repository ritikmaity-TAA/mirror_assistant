import asyncio, threading, os
from groq import AsyncGroq
from pathlib import Path
from core.config import GROQ_API_KEY

class Singleton(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):

        if cls in cls._instances:
            return cls._instances[cls]

        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]
    
class GroqClient(metaclass = Singleton):
    def __init__(self):
        self._client = None
        self._async_lock = None
        # threading.Lock guards the one-time creation of the asyncio.Lock itself.
        # The asyncio.Lock must be created inside a running event loop, so we
        # cannot create it here at import time (no loop exists yet).
        self._lock_creation_lock = threading.Lock()

    def _get_async_lock(self) -> asyncio.Lock:
        """
        Lazily creates the asyncio.Lock the first time it is needed,
        guaranteed to be inside a running event loop at that point.
        """
        if self._async_lock is None:
            with self._lock_creation_lock:
                if self._async_lock is None:
                    self._async_lock = asyncio.Lock()
        return self._async_lock

    async def get_client(self):
        """Lazily initialize the async Groq client.
        Safe for concurrent calls."""

        if self._client is not None:
            return self._client

        async with self._get_async_lock():
            if self._client is None:
                api_key = GROQ_API_KEY
                if not api_key:
                    raise RuntimeError("GROQ_API_KEY not set")

                self._client = AsyncGroq(api_key=api_key)

        return self._client

groqclient = GroqClient()