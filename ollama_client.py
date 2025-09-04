import httpx
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.models = ["gpt-oss-120b", "qwen3-32b", "deepseek-r1-0528"]
    
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
                return json.loads(result["response"])
                
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
