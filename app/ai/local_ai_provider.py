import requests
from app.ai.base_ai_provider import BaseAIProvider
import json

class LocalAIProvider(BaseAIProvider):
    """
    Provider for local LLMs compatible with OpenAI API (e.g., LM Studio, Ollama).
    """
    def __init__(self, api_key="lm-studio", base_url="http://localhost:1234/v1"):
        # API Key is often not needed for local servers but kept for compatibility
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')

    @staticmethod
    def get_provider_name():
        return "Local AI (LM Studio/Ollama)"

    def generate_text(self, prompt: str, max_tokens: int = 1500) -> str:
        """
        Generates text using the local LLM server.
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "messages": [
                {"role": "system", "content": "Eres un asistente ejecutivo eficiente y profesional. Tu objetivo es ayudar al usuario a procesar información, resumir textos y mejorar la redacción. Responde siempre en español de manera concisa."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "stream": False
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            else:
                return "Error: No se recibió respuesta del modelo local."

        except requests.exceptions.ConnectionError:
            return "Error: No se pudo conectar con el servidor de IA Local. Asegúrate de que LM Studio u Ollama estén ejecutándose en el puerto 1234."
        except Exception as e:
            return f"Error al generar texto: {str(e)}"
