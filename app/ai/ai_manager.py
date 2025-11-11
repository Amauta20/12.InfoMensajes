from app.db.settings_manager import SettingsManager
from app.security.vault_manager import VaultManager
from app.ai.base_ai_provider import BaseAIProvider
from app.ai.openai_provider import OpenAIProvider

# A mapping of provider names to their classes
SUPPORTED_PROVIDERS = {
    OpenAIProvider.get_provider_name(): OpenAIProvider,
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
            self._provider_instance = provider_class(api_key=api_key)

        except Exception:
            # If anything goes wrong (e.g., key not found, instantiation error),
            # ensure the provider is None.
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
        provider = self.get_current_provider()
        if provider is None:
            provider_name = self.settings_manager.get_ai_provider()
            if not provider_name:
                raise PermissionError("No AI provider has been configured in the settings.")
            elif self.vault_manager.is_locked():
                raise PermissionError("The Vault is locked. Please unlock it to use AI features.")
            else:
                raise PermissionError(f"AI Provider '{provider_name}' could not be loaded. Check API key and configuration.")

        # Here you could add logic to select a model from settings
        # model = self.settings_manager.get_ai_model() or "default-model"
        return provider.generate_text(prompt, max_tokens=max_tokens)
