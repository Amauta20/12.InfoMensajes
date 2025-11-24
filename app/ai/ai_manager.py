from app.db.settings_manager import SettingsManager
from app.security.vault_manager import VaultManager
from app.ai.base_ai_provider import BaseAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.local_ai_provider import LocalAIProvider
import hashlib
import logging

# A mapping of provider names to their classes
SUPPORTED_PROVIDERS = {
    OpenAIProvider.get_provider_name(): OpenAIProvider,
    LocalAIProvider.get_provider_name(): LocalAIProvider,
}

class AIManager:
    _instance = None

    @classmethod
    def initialize(cls, settings_manager: SettingsManager, vault_manager: VaultManager):
        if cls._instance is None:
            cls._instance = cls(settings_manager, vault_manager)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            raise Exception("AIManager singleton not initialized. Call initialize() first.")
        return cls._instance

    def __init__(self, settings_manager: SettingsManager, vault_manager: VaultManager):
        if self.__class__._instance is not None:
            raise Exception("This class is a singleton! Use get_instance() to get the instance.")
        
        self.settings_manager = settings_manager
        self.vault_manager = vault_manager
        self._provider_instance: BaseAIProvider | None = None
        
        # Cache configuration
        self._response_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        self._cache_enabled = True  # Default to enabled
        self._cache_size = 100  # Default cache size
        
        self._load_provider()

    def _load_provider(self):
        """Loads the AI provider based on user settings."""
        provider_name = self.settings_manager.get_ai_provider()
        
        if not provider_name or provider_name not in SUPPORTED_PROVIDERS:
            self._provider_instance = None
            return

        if self.vault_manager.is_locked():
            # If the vault is locked, we can't get the key. The provider remains None.
            self._provider_instance = None
            return

        try:
            secret_id = f"ai_api_key_{provider_name.lower()}"
            api_key = self.vault_manager.get_secret(secret_id)

            if not api_key:
                self._provider_instance = None
                return

            provider_class = SUPPORTED_PROVIDERS[provider_name]
            
            # Pass timeout configuration to providers
            if provider_name == LocalAIProvider.get_provider_name():
                timeout = 30  # Default local timeout
                self._provider_instance = provider_class(api_key=api_key, timeout=timeout)
            elif provider_name == OpenAIProvider.get_provider_name():
                timeout = 60  # Default OpenAI timeout
                self._provider_instance = provider_class(api_key=api_key, timeout=timeout)
            else:
                self._provider_instance = provider_class(api_key=api_key)

        except Exception as e:
            # If anything goes wrong (e.g., key not found, instantiation error),
            # ensure the provider is None.
            logging.error(f"Error loading AI provider: {e}", exc_info=True)
            self._provider_instance = None

    def get_current_provider(self) -> BaseAIProvider | None:
        """
        Returns the currently loaded AI provider instance.
        If the provider settings change, you might need to re-initialize AIManager
        or call a reload method. For simplicity, we load at init.
        """
        # Reload the provider in case the vault was unlocked after app start
        if self._provider_instance is None and not self.vault_manager.is_locked():
            self._load_provider()
        return self._provider_instance

    def _get_cache_key(self, prompt: str, max_tokens: int) -> str:
        """Generate a unique cache key for the prompt.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens for generation
            
        Returns:
            SHA256 hash of the prompt and parameters
        """
        content = f"{prompt}:{max_tokens}"
        return hashlib.sha256(content.encode()).hexdigest()

    def generate_text(self, prompt: str, max_tokens: int = 1500) -> str:
        """
        Generates text using the currently configured AI provider.

        Args:
            prompt: The input prompt for the AI.
            max_tokens: The maximum number of tokens for the output.

        Returns:
            The AI-generated text.

        Raises:
            PermissionError: If no provider is configured or available.
            Exception: For any errors during generation.
        """
        # Check cache first
        if self._cache_enabled:
            cache_key = self._get_cache_key(prompt, max_tokens)
            if cache_key in self._response_cache:
                self._cache_hits += 1
                logging.debug(f"Cache hit for prompt (key: {cache_key[:8]}...)")
                return self._response_cache[cache_key]
            self._cache_misses += 1
        
        provider = self.get_current_provider()
        if provider is None:
            provider_name = self.settings_manager.get_ai_provider()
            if not provider_name:
                raise PermissionError("No AI provider has been configured in the settings.")
            elif self.vault_manager.is_locked():
                raise PermissionError("The Vault is locked. Please unlock it to use AI features.")
            else:
                raise PermissionError(f"AI Provider '{provider_name}' could not be loaded. Check API key and configuration.")

        # Generate response
        response = provider.generate_text(prompt, max_tokens=max_tokens)
        
        # Store in cache
        if self._cache_enabled:
            # Implement simple FIFO eviction if cache is full
            if len(self._response_cache) >= self._cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self._response_cache))
                del self._response_cache[oldest_key]
                logging.debug(f"Cache full, evicted oldest entry")
            self._response_cache[cache_key] = response
            logging.debug(f"Cached response (key: {cache_key[:8]}...)")
        
        return response

    def clear_cache(self):
        """Clear the response cache and reset statistics."""
        self._response_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logging.info("AI response cache cleared")

    def get_cache_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache hits, misses, size, and hit rate
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total * 100) if total > 0 else 0
        return {
            'hits': self._cache_hits,
            'misses': self._cache_misses,
            'size': len(self._response_cache),
            'hit_rate': round(hit_rate, 2)
        }

    def set_cache_enabled(self, enabled: bool):
        """Enable or disable response caching.
        
        Args:
            enabled: True to enable caching, False to disable
        """
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        logging.info(f"AI cache {'enabled' if enabled else 'disabled'}")

    def set_cache_size(self, size: int):
        """Set the maximum cache size.
        
        Args:
            size: Maximum number of cached responses
        """
        if size < 1:
            size = 1
        self._cache_size = size
        
        # Trim cache if new size is smaller
        while len(self._response_cache) > self._cache_size:
            oldest_key = next(iter(self._response_cache))
            del self._response_cache[oldest_key]
        
        logging.info(f"AI cache size set to {size}")

