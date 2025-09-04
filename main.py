from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

from sgr_schema import SQLGeneration, DATABASE_SCHEMA, EXAMPLE_QUERIES
from database import DatabaseManager  
from ollama_client import OllamaClient

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные объекты
db_manager = DatabaseManager()
ollama_client = OllamaClient(os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for startup and shutdown"""
    await db_manager.initialize()
    logger.info("Приложение запущено")
    try:
        yield
    finally:
        await db_manager.close()


app = FastAPI(title="Text2SQL POC с SGR", version="1.0.0", lifespan=lifespan)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

class QueryRequest(BaseModel):
    question: str
    model: str = "qwen3-32b"

class QueryResponse(BaseModel):
    sql_query: str
    explanation: str
    confidence: float
    results: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: int
    model_used: str

    model_config = {"protected_namespaces": ()}

@app.get("/", response_class=HTMLResponse)
async def root():
    """Главная страница"""
    index_path = BASE_DIR / "static" / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/models")
async def get_available_models():
    """Получение списка доступных моделей"""
    available = []
    for model in ollama_client.models:
        is_available = await ollama_client.check_model_availability(model)
        available.append({"name": model, "available": is_available})
    return {"models": available}

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Обработка естественного запроса"""
    import time
    start_time = time.time()
    
    try:
        # Создание промпта для SGR
        prompt = f"""
Ты эксперт по SQL и работе с базами данных. Твоя задача - преобразовать естественный запрос на русском языке в корректный SQL запрос.

СХЕМА БАЗЫ ДАННЫХ:
{DATABASE_SCHEMA}

ПРИМЕРЫ ЗАПРОСОВ:
{chr(10).join(EXAMPLE_QUERIES)}

ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС: "{request.question}"

Следуй Schema-Guided Reasoning подходу:
1. Проанализируй запрос пользователя
2. Определи стратегию построения SQL
3. Сгенерируй корректный SQL запрос
4. Объясни логику

ВАЖНО:
- Используй только SELECT запросы
- Все названия полей в двойных кавычках
- Для текстового поиска используй ILIKE '%term%'
- Для номенклатуры ищи по двум полям: ("Nomenclature" ILIKE '%term%' OR "NomenclatureFullName" ILIKE '%term%')
- Добавь LIMIT 50 если не указано иначе
"""

        # Получение схемы для структурированного вывода
        schema = SQLGeneration.model_json_schema()
        
        # Генерация ответа
        result = await ollama_client.generate_structured(
            model=request.model,
            prompt=prompt,
            schema=schema,
            temperature=0.2
        )
        
        # Парсинг результата
        sgr_result = SQLGeneration(**result)
        
        # Выполнение SQL запроса
        query_results = await db_manager.execute_query(sgr_result.sql_query)
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return QueryResponse(
            sql_query=sgr_result.sql_query,
            explanation=sgr_result.explanation,
            confidence=sgr_result.confidence_score,
            results=query_results,
            execution_time_ms=execution_time,
            model_used=request.model
        )
        
    except Exception as e:
        logger.error(f"Ошибка обработки запроса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
