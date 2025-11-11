from abc import ABC, abstractmethod

class BaseAIProvider(ABC):
    """
    Abstract base class for all AI providers.
    It defines the common interface that all concrete providers must implement.
    """

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 150) -> str:
        """
        Generates text based on a given prompt.

        Args:
            prompt: The input text to the AI model.
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text as a string.
        
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
            Exception: For any errors during the API call.
        """
        raise NotImplementedError

    @staticmethod
    def get_provider_name() -> str:
        """
        Returns the name of the provider.
        
        Raises:
            NotImplementedError: If the method is not implemented by the subclass.
        """
        raise NotImplementedError
