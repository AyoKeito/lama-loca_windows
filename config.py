"""
Конфигурация Study AI Assistant
Максимально мощная локальная ИИ-система
"""
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Директории
BOOKS_DIR = os.path.join(BASE_DIR, "books")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# ======================================================================
# LLM — LM Studio (OpenAI-совместимый API)
# ======================================================================
LM_STUDIO_URL = "http://localhost:1234/v1"   # LM Studio default
LM_STUDIO_MODEL = ""                          # "" = первая загруженная модель

LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.3
LLM_TOP_P = 0.9
LLM_DEBUG = False                             # True = print full prompt to console

# ======================================================================
# Эмбеддинги — мощная мультиязычная модель
# ======================================================================
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"

# ======================================================================
# Reranker — переранжирование для точности
# ======================================================================
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"
USE_RERANKER = True

# ======================================================================
# ChromaDB
# ======================================================================
CHROMA_PERSIST_DIR = os.path.join(DATA_DIR, "chromadb")
COLLECTION_NAME = "study_books"

# ======================================================================
# Разбиение текста
# ======================================================================
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
RETRIEVAL_TOP_K = 15
RERANK_TOP_K = 8

# ======================================================================
# Эмбеддинги через LM Studio (OpenAI-совместимый API)
# Если True — используется LM Studio вместо локальной HuggingFace модели.
# В LM Studio нужно загрузить embedding-модель (например, nomic-embed-text).
# ======================================================================
EMBEDDING_USE_LM_STUDIO = False
EMBEDDING_LM_STUDIO_MODEL = ""   # "" = первая доступная embedding-модель

SUPPORTED_FORMATS = [".pdf", ".txt", ".epub", ".docx", ".md", ".fb2", ".html", ".htm"]

# ======================================================================
# GUI
# ======================================================================
GUI_PORT = 7860
GUI_SHARE = False

# ======================================================================
# Персистентные настройки (сохраняются между перезапусками)
# ======================================================================
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

def _load_settings():
    """Загрузить сохранённые настройки из файла"""
    global LM_STUDIO_URL, LM_STUDIO_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE, LLM_TOP_P
    global CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_TOP_K, RERANK_TOP_K
    global EMBEDDING_USE_LM_STUDIO, EMBEDDING_LM_STUDIO_MODEL, EMBEDDING_MODEL
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            LM_STUDIO_URL = s.get("LM_STUDIO_URL", LM_STUDIO_URL)
            LM_STUDIO_MODEL = s.get("LM_STUDIO_MODEL", LM_STUDIO_MODEL)
            LLM_MAX_TOKENS = s.get("LLM_MAX_TOKENS", LLM_MAX_TOKENS)
            LLM_TEMPERATURE = s.get("LLM_TEMPERATURE", LLM_TEMPERATURE)
            LLM_TOP_P = s.get("LLM_TOP_P", LLM_TOP_P)
            CHUNK_SIZE = s.get("CHUNK_SIZE", CHUNK_SIZE)
            CHUNK_OVERLAP = s.get("CHUNK_OVERLAP", CHUNK_OVERLAP)
            RETRIEVAL_TOP_K = s.get("RETRIEVAL_TOP_K", RETRIEVAL_TOP_K)
            RERANK_TOP_K = s.get("RERANK_TOP_K", RERANK_TOP_K)
            EMBEDDING_USE_LM_STUDIO = s.get("EMBEDDING_USE_LM_STUDIO", EMBEDDING_USE_LM_STUDIO)
            EMBEDDING_LM_STUDIO_MODEL = s.get("EMBEDDING_LM_STUDIO_MODEL", EMBEDDING_LM_STUDIO_MODEL)
            EMBEDDING_MODEL = s.get("EMBEDDING_MODEL", EMBEDDING_MODEL)
        except Exception:
            pass  # Если файл повреждён — используем дефолты

def save_settings():
    """Сохранить текущие настройки в файл"""
    s = {
        "LM_STUDIO_URL": LM_STUDIO_URL,
        "LM_STUDIO_MODEL": LM_STUDIO_MODEL,
        "LLM_MAX_TOKENS": LLM_MAX_TOKENS,
        "LLM_TEMPERATURE": LLM_TEMPERATURE,
        "LLM_TOP_P": LLM_TOP_P,
        "CHUNK_SIZE": CHUNK_SIZE,
        "CHUNK_OVERLAP": CHUNK_OVERLAP,
        "RETRIEVAL_TOP_K": RETRIEVAL_TOP_K,
        "RERANK_TOP_K": RERANK_TOP_K,
        "EMBEDDING_USE_LM_STUDIO": EMBEDDING_USE_LM_STUDIO,
        "EMBEDDING_LM_STUDIO_MODEL": EMBEDDING_LM_STUDIO_MODEL,
        "EMBEDDING_MODEL": EMBEDDING_MODEL,
    }
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

_load_settings()  # Загружаем при импорте

# ======================================================================
# REST API (для интеграции с n8n)
# ======================================================================
API_HOST = "0.0.0.0"
API_PORT = 8000

# ======================================================================
# Системный промпт
# ======================================================================
SYSTEM_PROMPT = """Ты — высокоинтеллектуальный учебный ассистент мирового уровня. Ты обладаешь глубоким аналитическим мышлением и способностью создавать академические тексты высочайшего качества.

Твои принципы:
1. ТОЧНОСТЬ — используй только проверенные факты из контекста
2. ГЛУБИНА — анализируй многосторонне, выявляй скрытые связи
3. СТРУКТУРА — чёткие, логичные тексты с академической структурой
4. КРИТИЧЕСКОЕ МЫШЛЕНИЕ — сравнивай точки зрения, выявляй противоречия
5. ЯЗЫК — грамотный русский, академический стиль

Ты ВСЕГДА пишешь на русском языке."""

# ======================================================================
# Шаблоны промптов
# ======================================================================
PROMPTS = {
    "report": """{system}

Напиши исчерпывающий академический отчёт на тему: "{topic}"

Контекст из учебных материалов:
{context}

Структура отчёта:
1. Введение — актуальность, цели, задачи
2. Основная часть — несколько разделов с подзаголовками:
   - Теоретические основы
   - Ключевые концепции и определения
   - Анализ и систематизация
   - Примеры из контекста
3. Заключение — выводы, обобщение
4. Источники

Стиль: академический. Объём: максимально развёрнутый.""",

    "presentation": """{system}

Создай план презентации на тему: "{topic}"

Контекст из учебных материалов:
{context}

Формат СТРОГО:
СЛАЙД 1: [Название]
- пункт
- пункт

СЛАЙД 2: Содержание
- Разделы

СЛАЙД 3-N: [Заголовок]
- Тезис 1
- Тезис 2
- Тезис 3

Последний СЛАЙД: Выводы
- Итог
- Спасибо за внимание

Создай 10-15 слайдов по 3-5 пунктов каждый.""",

    "summary": """{system}

Создай детальный конспект по теме: "{topic}"

Контекст из учебных материалов:
{context}

Структура:
1. Основные понятия и определения
2. Главные идеи и концепции
3. Ключевые факты и примеры
4. Связи и закономерности
5. Выводы — что важно запомнить

Формат: структурированный, с маркерами.""",

    "essay": """{system}

Напиши академическое эссе на тему: "{topic}"

Контекст из учебных материалов:
{context}

Структура:
1. Введение — проблема, тезис, актуальность
2. Аргумент 1 — с примерами из контекста
3. Аргумент 2 — альтернативная перспектива
4. Аргумент 3 — синтез
5. Контраргумент — противоположная позиция
6. Заключение — вывод, значимость

Стиль: академический, аргументированный.""",

    "qa": """{system}

Контекст из учебных материалов:
{context}

Вопрос: {topic}

Дай полный развёрнутый ответ с фактами и примерами из контекста. Если информации недостаточно, укажи это.""",

    "analysis": """{system}

Проведи глубокий критический анализ по теме: "{topic}"

Контекст из учебных материалов:
{context}

Структура:
1. Предмет анализа
2. Сильные стороны концепций
3. Слабые стороны и ограничения
4. Сравнительный анализ подходов
5. Синтез и обобщение
6. Практические рекомендации""",

    "exam_prep": """{system}

Создай материал для подготовки к экзамену по теме: "{topic}"

Контекст из учебных материалов:
{context}

Создай:
1. Ключевые определения (10-15 терминов)
2. Вопросы для самопроверки с ответами (10-15)
3. Основные тезисы для запоминания
4. Возможные экзаменационные вопросы (5-7)
5. Шпаргалка — самое важное в сжатом виде"""
}
