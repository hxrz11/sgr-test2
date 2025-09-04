import asyncpg
import os
import time
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.pool = None
    
    def _build_connection_string(self) -> str:
        return (
            f"postgresql://"
            f"{os.getenv('DATABASE_USER')}:"
            f"{os.getenv('DATABASE_PASSWORD')}@"
            f"{os.getenv('DATABASE_HOST', 'localhost')}:"
            f"{os.getenv('DATABASE_PORT', 5432)}/"
            f"{os.getenv('DATABASE_NAME')}"
        )
    
    async def initialize(self):
        """Инициализация пула соединений"""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10,
                command_timeout=30
            )
            logger.info("Подключение к базе данных установлено")
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise
    
    async def execute_query(self, sql: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса с ограничениями безопасности"""
        
        # Базовая валидация SQL
        sql_lower = sql.lower().strip()
        
        # Запрещенные операции
        forbidden = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
        if any(word in sql_lower for word in forbidden):
            raise ValueError("Запрещены операции изменения данных")
        
        # Обязательное указание таблицы
        if 'purchaseallview' not in sql_lower:
            raise ValueError("Запросы должны использовать таблицу PurchaseAllView")
        
        # Добавление LIMIT если отсутствует
        if 'limit' not in sql_lower:
            sql += f" LIMIT {limit}"

        logger.info("Executing SQL: %s", sql)

        try:
            async with self.pool.acquire() as connection:
                start_time = time.perf_counter()
                result = await connection.fetch(sql)
                duration = time.perf_counter() - start_time
                logger.info("SQL execution took %.3f seconds", duration)
                return [dict(row) for row in result]
                
        except Exception as e:
            logger.error(f"Ошибка выполнения SQL: {e}")
            raise ValueError(f"Ошибка SQL: {str(e)}")
    
    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
