import os
import time
import logging
from typing import List, Dict, Any

import asyncpg
import dotenv
import re

dotenv.load_dotenv()

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
    
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса с ограничениями безопасности"""

        # Предварительная нормализация запроса
        sql = self._normalize_query(sql)

        # Базовая валидация SQL
        sql_lower = sql.lower().strip()
        
        # Запрещенные операции
        forbidden = ['insert', 'update', 'delete', 'drop', 'create', 'alter', 'truncate']
        if any(word in sql_lower for word in forbidden):
            raise ValueError("Запрещены операции изменения данных")
        
        # Обязательное указание таблицы
        if 'purchaseallview' not in sql_lower:
            raise ValueError("Запросы должны использовать таблицу PurchaseAllView")

        # Корректное написание названия таблицы
        if '"purchaseallview"' not in sql_lower:
            sql = re.sub(r'(?i)purchaseallview', '"PurchaseAllView"', sql)
        
        # Не добавляем LIMIT автоматически, выполняем запрос как есть

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

    def _normalize_query(self, sql: str) -> str:
        """Исправляет распространённые ошибки в сгенерированных запросах"""

        def normalize_term(term: str) -> str:
            """Убирает окончания у русских слов для более широкого поиска"""
            return re.sub(r'[аяыиоеёюу]+$', '', term, flags=re.IGNORECASE)

        # Нормализация шаблонов ILIKE '%term%'
        def replace_ilike(match: re.Match) -> str:
            term = match.group(1)
            return f"ILIKE '%{normalize_term(term)}%'"

        sql = re.sub(r"ILIKE\s*'%([^']+)%'", replace_ilike, sql, flags=re.IGNORECASE)

        # Приведение числовых полей к numeric при сравнении
        def replace_numeric(match: re.Match) -> str:
            field, operator, value = match.groups()
            return f'CAST("{field}" AS numeric) {operator} {value}'

        numeric_fields = ['Quantity', 'RemainingQuantity', 'ProcessedQuantity']
        pattern = r'"(' + '|'.join(numeric_fields) + r')"\s*([<>]=?)\s*(\d+(?:\.\d+)?)'
        sql = re.sub(pattern, replace_numeric, sql, flags=re.IGNORECASE)

        return sql
