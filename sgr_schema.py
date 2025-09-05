from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime

class QueryAnalysis(BaseModel):
    """Анализ пользовательского запроса"""
    user_intent: str = Field(description="Понимание намерений пользователя")
    key_entities: List[str] = Field(description="Ключевые сущности: номер заявки, номенклатура, пользователь, объект")
    search_terms: List[str] = Field(description="Термины для поиска в текстовых полях")
    date_references: Optional[str] = Field(description="Упоминания дат или периодов")
    quantity_filters: Optional[str] = Field(description="Условия по количеству")

class SQLStrategy(BaseModel):
    """Стратегия построения SQL запроса"""
    query_type: Literal["simple_select", "filtered_select", "aggregation", "grouping", "complex_join"]
    target_fields: List[str] = Field(description="Поля для SELECT (используй точные названия из схемы)")
    where_conditions: List[str] = Field(description="Логические условия WHERE")
    grouping_fields: Optional[List[str]] = Field(description="Поля для GROUP BY, если нужно")
    ordering: Optional[str] = Field(description="Сортировка ORDER BY")
    requires_aggregation: bool = Field(description="Нужны ли COUNT, SUM, MAX и т.д.")

class SQLGeneration(BaseModel):
    """Финальная генерация SQL с объяснением"""
    analysis: QueryAnalysis
    strategy: SQLStrategy
    sql_query: str = Field(description="Готовый SQL запрос для PostgreSQL")
    explanation: str = Field(description="Объяснение логики запроса на русском")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Уверенность в корректности от 0 до 1")
    potential_issues: Optional[str] = Field(description="Возможные проблемы или ограничения")

# Схема базы данных для промптов
DATABASE_SCHEMA = """
Таблица: "PurchaseAllView" (PostgreSQL)

Поля:
- "GlobalUid" (text) - Уникальный идентификатор записи
- "OrderNumber" (text) - Номер заявки (например: ЛГ000000524)  
- "OrderDate" (timestamp) - Дата создания заявки
- "ApprovalDate" (timestamp) - Дата утверждения заявки
- "ObjectName" (text) - Название объекта строительства
- "Nomenclature" (text) - Краткое название номенклатуры
- "NomenclatureFullName" (text) - Полное название номенклатуры
- "ArtNumber" (text) - Артикул товара
- "Quantity" (numeric) - Количество заказанное
- "RemainingQuantity" (numeric) - Остаток количества
- "ProcessedQuantity" (numeric) - Обработанное количество
- "UnitName" (text) - Единица измерения (шт, м, кг и т.д.)
- "ProcessingDate" (timestamp) - Дата обработки
- "CompletedDate" (timestamp) - Дата завершения
- "UserName" (text) - Логин пользователя
- "Notes" (text) - Примечания
- "ArchiveStatus" (text) - Статус архивации
- "PurchaseRecordStatus" (text) - Статус записи закупки (A=активный)
- "PurchaseCardId" (uuid) - ID карточки закупки
- "PurchaseNumber" (text) - Номер закупки
- "PurchaseCardDate" (timestamp) - Дата создания карточки закупки
- "PurchaseCardUserName" (text) - Логин пользователя
- "PurchaseCardFio" (text) - ФИО пользователя

ВАЖНЫЕ ПРАВИЛА:
1. Используй ILIKE '%term%' для нечеткого поиска
2. Для поиска по номенклатуре ищи по обоим полям: ("Nomenclature" ILIKE '%term%' OR "NomenclatureFullName" ILIKE '%term%')
3. Все названия полей и таблицы в двойных кавычках
4. Даты в формате YYYY-MM-DD
5. Для поиска пользователей ищи по трём полям: ("UserName" ILIKE '%term%' OR "PurchaseCardUserName" ILIKE '%term%' OR "PurchaseCardFio" ILIKE '%term%')
"""

EXAMPLE_QUERIES = [
    "Найди закупки по 105 заявке → WHERE \"OrderNumber\" ILIKE '%105%'",
    "Найди номенклатуры с лампами → WHERE (\"Nomenclature\" ILIKE '%лампа%' OR \"NomenclatureFullName\" ILIKE '%лампа%')",
    "Сколько позиций у Петрова в работе → WHERE (\"UserName\" ILIKE '%Petrov%' OR \"PurchaseCardUserName\" ILIKE '%Petrov%' OR \"PurchaseCardFio\" ILIKE '%Petrov%') AND \"RemainingQuantity\" > 0",
    "Покажи заявки по объекту Газопровод → WHERE \"ObjectName\" ILIKE '%Газопровод%'"
]
