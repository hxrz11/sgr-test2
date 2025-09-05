# Установка моделей Ollama
## Установка моделей
ollama pull deepseek-r1:32b
ollama pull qwen3:32b
ollama pull gpt-oss:20b
ollama pull fomenks/T-Pro-1.0-it-q4_k_m:latest

## Проверка установленных моделей
ollama list

## Тестирование модели
ollama run qwen3:32b

# Запуск POC
## 1. Установка зависимостей
pip install -r requirements.txt

## 2. Настройка базы данных в .env
cp .env.example .env
## Отредактировать параметры подключения

## 3. Запуск приложения
python main.py

## Или через uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Особенности реализации
SGR Pipeline:
Analysis - анализ намерений и сущностей
Strategy - выбор подхода к построению SQL
Generation - создание SQL с объяснением
Validation - проверка безопасности и выполнение

Безопасность:
Только SELECT запросы
Валидация на уровне БД
Ограничение количества результатов
Санитизация входных данных

A/B Тестирование:
4 модели для сравнения качества
Метрики времени выполнения
Оценка уверенности модели

Приложение готово к запуску! Интерфейс доступен по адресу http://localhost:8000
