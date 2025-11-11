import openai
from app.ai.base_ai_provider import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    """
    Concrete implementation of the AI provider for OpenAI.
    """
    PROVIDER_NAME = "OpenAI"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key for OpenAI cannot be empty.")
        self.api_key = api_key
        self.client = openai.OpenAI(api_key=self.api_key)

    @staticmethod
    def get_provider_name() -> str:
        return OpenAIProvider.PROVIDER_NAME

    def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", max_tokens: int = 1500) -> str:
        """
        Generates text using the OpenAI API.

        Args:
            prompt: The input text to the AI model.
            model: The specific model to use (e.g., "gpt-3.5-turbo").
            max_tokens: The maximum number of tokens to generate.

        Returns:
            The generated text as a string.
        
        Raises:
            Exception: For any errors during the API call.
        """
        if not self.api_key:
            raise PermissionError("OpenAI API key is not configured.")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                n=1,
                stop=None,
                temperature=0.7,
            )
            if response.choices:
                return response.choices[0].message.content.strip()
            else:
                raise Exception("OpenAI API call did not return any choices.")
        except Exception as e:
            # Log the error or handle it as needed
            print(f"An error occurred with the OpenAI API: {e}")
            raise
