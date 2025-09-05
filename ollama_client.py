import httpx
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.models = [
            "deepseek-r1:32b",
            "qwen3:32b",
            "gpt-oss:20b",
            "fomenks/T-Pro-1.0-it-q4_k_m:latest",
        ]
    
    async def generate_structured(self, model: str, prompt: str, schema: Dict[str, Any], temperature: float = 0.2) -> Dict[str, Any]:
        """Генерация с структурированным выводом"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": schema,
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_ctx": 8192
                    }
                }
                
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                
                result = response.json()
                try:
                    return json.loads(result["response"])
                except json.JSONDecodeError as e:
                    logger.error(f"Некорректный JSON в ответе модели: {result.get('response')}")
                    raise ValueError("Модель вернула некорректный JSON") from e
                
        except Exception as e:
            logger.error(f"Ошибка генерации с моделью {model}: {e}")
            raise

    async def check_model_availability(self, model: str) -> bool:
        """Проверка доступности модели"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    return any(m["name"].startswith(model) for m in models)
                return False
        except:
            return False
