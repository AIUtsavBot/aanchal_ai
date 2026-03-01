"""
Gemini API Key Rotator
Automatically rotates between multiple Gemini API keys when one hits rate limits (429).
Add up to 3 keys in .env as GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3
"""

import os
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiKeyRotator:
    """
    Thread-safe round-robin Gemini API key rotator.
    Falls back to the next key automatically on 429 / quota errors.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._keys = self._load_keys()
        self._index = 0
        self._clients: dict[str, object] = {}

        if self._keys:
            logger.info(f"✅ GeminiKeyRotator initialized with {len(self._keys)} key(s)")
        else:
            logger.warning("⚠️ GeminiKeyRotator: No GEMINI_API_KEY found in environment")

    # ------------------------------------------------------------------
    def _load_keys(self) -> list[str]:
        keys = []
        for env_var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
            k = os.getenv(env_var, "").strip()
            if k:
                keys.append(k)
        return keys

    def _get_client(self, key: str):
        """Return (or create) a cached genai.Client for a given key."""
        if not GENAI_AVAILABLE:
            return None
        if key not in self._clients:
            self._clients[key] = genai.Client(api_key=key)
        return self._clients[key]

    # ------------------------------------------------------------------
    @property
    def current_client(self):
        """Return the currently active Gemini client."""
        if not self._keys:
            return None
        with self._lock:
            return self._get_client(self._keys[self._index])

    def rotate(self):
        """Advance to the next key (called automatically on 429)."""
        with self._lock:
            if not self._keys:
                return
            prev_index = self._index
            self._index = (self._index + 1) % len(self._keys)
            logger.warning(
                f"🔄 Gemini key rotated: key[{prev_index}] → key[{self._index}]"
            )

    # ------------------------------------------------------------------
    def generate_content(self, model: str, contents, config=None):
        """
        Wrapper around genai.Client.models.generate_content that auto-rotates on 429.
        """
        last_error = None
        for attempt in range(len(self._keys) or 1):
            client = self.current_client
            if not client:
                break
            try:
                kwargs = {"model": model, "contents": contents}
                if config:
                    kwargs["config"] = config
                return client.models.generate_content(**kwargs)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    logger.warning(f"⚠️ Rate limit on key[{self._index}]: rotating…")
                    self.rotate()
                    last_error = e
                else:
                    raise  # Non-quota errors bubble up immediately
        raise last_error or RuntimeError("All Gemini API keys exhausted")

    def embed_content(self, model: str, contents):
        """
        Wrapper around genai.Client.models.embed_content that auto-rotates on 429.
        """
        last_error = None
        for attempt in range(len(self._keys) or 1):
            client = self.current_client
            if not client:
                break
            try:
                return client.models.embed_content(model=model, contents=contents)
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    logger.warning(f"⚠️ Rate limit on key[{self._index}] (embed): rotating…")
                    self.rotate()
                    last_error = e
                else:
                    raise
        raise last_error or RuntimeError("All Gemini API keys exhausted (embed)")

    # ------------------------------------------------------------------
    @property
    def is_available(self) -> bool:
        return GENAI_AVAILABLE and bool(self._keys)


# Module-level singleton — import this everywhere
gemini_rotator = GeminiKeyRotator()
