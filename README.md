<div align="center">

# 📚 Lama Loca — Study AI Assistant

### Локальный ИИ, который учится по вашим книгам

[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Gradio](https://img.shields.io/badge/GUI-Gradio-orange.svg)](https://gradio.app)
[![LLM](https://img.shields.io/badge/LLM-Qwen2.5-purple.svg)](https://huggingface.co/Qwen)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-blue.svg)](https://microsoft.com/windows)
[![API](https://img.shields.io/badge/API-FastAPI-green.svg)](https://fastapi.tiangolo.com)

**Загрузи свои учебники → Получи отчёты, презентации, конспекты и ответы на вопросы**

*Всё работает полностью офлайн. Ваши данные не покидают компьютер.*

</div>

---

## ✨ Возможности

| | Функция | Описание |
|:---:|---------|----------|
| | Функция | Описание |
|:---:|---------|----------|
| 💬 | **Чат** | Задавайте вопросы по книгам — ответы в реальном времени (стриминг) |
| 📝 | **Отчёты** | Академические отчёты с введением, анализом и выводами (DOCX + MD) |
| 📊 | **Презентации** | Готовые PowerPoint-файлы (PPTX) с 10-15 слайдами |
| 📋 | **Конспекты** | Структурированные конспекты с ключевыми тезисами |
| ✍️ | **Эссе** | Академические эссе с аргументацией и контраргументами |
| 🔬 | **Критический анализ** | Глубокий разбор темы: сильные/слабые стороны, выводы |
| 📖 | **Подготовка к экзаменам** | Определения, вопросы с ответами, шпаргалки |
| 🔌 | **REST API** | Интеграция с n8n, Make, Zapier и другими сервисами автоматизации |

---

## 🏗️ Архитектура

```
  📚 Книги (PDF / EPUB / DOCX / TXT / FB2 / HTML / MD)
         │
         ▼
  ┌──────────────┐
  │  📄 Парсер   │   Загрузка и извлечение текста
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  ✂️ Чанкинг  │   Разбиение на фрагменты (1500 символов, overlap 300)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  🧠 E5-Large │   Мультиязычные эмбеддинги (intfloat/multilingual-e5-large)
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  💾 ChromaDB │   Персистентная векторная база данных
  └──────┬───────┘
         │
    Запрос пользователя ──────────────┐
         │                            │
         ▼                            ▼
  ┌──────────────┐           ┌──────────────┐
  │  🔍 Поиск    │  Top-15   │  🎯 Reranker │  Cross-Encoder → Top-8
  └──────┬───────┘           └──────┬───────┘
         │                          │
         └──────────┬───────────────┘
                    ▼
             ┌──────────────┐
             │  🤖 LLM      │   Qwen2.5 (до 32B), контекст 32K
             └──────┬───────┘
                    ▼
             ┌──────────────┐
             │  📁 Экспорт  │   DOCX / PPTX / Markdown
             └──────────────┘
```

---

## 🚀 Быстрый старт

### 1. Клонирование и установка

**Linux / macOS:**
```bash
git clone https://github.com/emil-a-dev/lama-loca.git
cd lama-loca
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
git clone https://github.com/emil-a-dev/lama-loca.git
cd lama-loca
setup.bat
```

Скрипт установки автоматически:
- Создаст виртуальное окружение
- Установит все зависимости
- Предложит скачать оптимальную модель

### 2. Запуск

**Linux / macOS:**
```bash
source venv/bin/activate
python main.py
```

**Windows:**
```cmd
venv\Scripts\activate
python main.py
```

- GUI откроется в браузере на `http://localhost:7860`
- REST API будет доступно на `http://localhost:8000` (документация: `http://localhost:8000/docs`)

### 3. Использование

1. **Вкладка «Книги»** — загрузите свои учебники (drag & drop)
2. **Нажмите «Индексировать»** — система проанализирует и запомнит содержимое
3. **Задавайте вопросы** в чате или **создавайте документы** по темам из книг

---

## 🔥 Что делает систему мощной

| Компонент | Технология | Эффект |
|:---------:|-----------|--------|
| 🤖 **LLM** | Qwen2.5 до 32B (GGUF, квантизация Q4_K_M) | Генерация текста на уровне коммерческих моделей |
| 📐 **Контекст** | 32 768 токенов | Модель «видит» и анализирует огромные объёмы текста |
| 🧠 **Эмбеддинги** | E5-Large Multilingual | Высокоточный семантический поиск на русском |
| 🎯 **Реранкер** | Cross-Encoder (ms-marco) | Точная фильтрация: из 15 кандидатов → 8 лучших |
| 🎛️ **Sampling** | temp=0.3, top_p=0.9, repeat_penalty=1.15 | Точные, связные, не повторяющиеся ответы |
| 🖥️ **GUI** | Gradio (веб-интерфейс) | Удобная работа без командной строки |
| 🔌 **API** | FastAPI + uvicorn | REST API для автоматизации через n8n и другие сервисы |

---

## 📦 Рекомендуемые модели

| Модель | Размер | RAM | Качество |
|--------|--------|-----|----------|
| **Qwen2.5-32B-Instruct** Q4_K_M | ~20 GB | 24+ GB | 🏆 Максимальное |
| **Qwen2.5-14B-Instruct** Q4_K_M | ~9 GB | 12+ GB | ⭐ Отличное |
| **Qwen2.5-7B-Instruct** Q4_K_M | ~5 GB | 8+ GB | 👍 Хорошее |
| **Qwen2.5-3B-Instruct** Q4_K_M | ~2.5 GB | 4+ GB | Базовое |

> 💡 Скрипты `setup.sh` (Linux/macOS) и `setup.bat` (Windows) рекомендуют оптимальную модель и предлагают скачать её автоматически.

### Ручная установка модели

**Linux / macOS:**
```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF \
    qwen2.5-14b-instruct-q4_k_m.gguf \
    --local-dir models/ --local-dir-use-symlinks False
mv models/qwen2.5-14b-instruct-q4_k_m.gguf models/model.gguf
```

**Windows:**
```cmd
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF ^
    qwen2.5-14b-instruct-q4_k_m.gguf ^
    --local-dir models/ --local-dir-use-symlinks False
move models\qwen2.5-14b-instruct-q4_k_m.gguf models\model.gguf
```

---

## 📂 Структура проекта

```
lama-loca/
├── main.py                        # 🖥️ GUI (Gradio) + запуск REST API
├── config.py                      # ⚙️ Все настройки
├── setup.sh                       # 📦 Скрипт установки (Linux/macOS)
├── setup.bat                      # 📦 Скрипт установки (Windows)
├── requirements.txt               # 📋 Зависимости Python
├── src/
│   ├── llm_engine.py              # 🤖 LLM движок (llama-cpp-python)
│   ├── knowledge_base.py          # 🧠 RAG + Reranker + ChromaDB
│   ├── api.py                     # 🔌 REST API для n8n (FastAPI)
│   ├── document_generator.py      # 📝 Генератор DOCX / Markdown
│   └── presentation_generator.py  # 📊 Генератор PPTX
├── books/                         # 📚 Ваши книги (не в git)
├── models/                        # 🤖 GGUF модель (не в git)
├── output/                        # 📁 Готовые документы (не в git)
└── data/                          # 💾 Векторная БД (не в git)
```

---

## 🔌 REST API для n8n

При запуске `python main.py` автоматически стартует REST API на порту `8000`.

**Swagger-документация:** `http://localhost:8000/docs`

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/health` | Проверка состояния |
| GET | `/api/stats` | Статистика базы знаний |
| POST | `/api/chat` | Вопрос-ответ по книгам |
| POST | `/api/generate` | Генерация документа |
| POST | `/api/presentation` | Генерация презентации |
| POST | `/api/index` | Индексировать книги из `books/` |
| POST | `/api/books/upload` | Загрузить и проиндексировать файл |
| DELETE | `/api/knowledge-base` | Очистить базу знаний |
| GET | `/api/files` | Список готовых документов |
| GET | `/api/files/{filename}` | Скачать документ |

### Примеры для n8n (HTTP Request node)

**Задать вопрос:**
```json
POST http://localhost:8000/api/chat
{ "message": "Что такое фотосинтез?" }
```

**Сгенерировать отчёт:**
```json
POST http://localhost:8000/api/generate
{ "topic": "Термодинамика", "doc_type": "report", "format": "md" }
```

Поле `doc_type`: `report` | `summary` | `essay` | `analysis` | `exam_prep`

**Изменить порт API** в `config.py`:
```python
API_PORT = 8000  # любой свободный порт
```

---

## ⚡ GPU ускорение

По умолчанию все слои модели загружаются на GPU (`LLM_GPU_LAYERS = -1`).

**Нет GPU?** В `config.py`:
```python
LLM_GPU_LAYERS = 0  # только CPU
```

**NVIDIA GPU + CUDA:**
```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir \
    -C cmake.args="-DGGML_CUDA=ON"
```

---

## 🛠️ Настройка

Все параметры в [`config.py`](config.py):

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| `LLM_CONTEXT_SIZE` | 32768 | Размер контекста (токены) |
| `LLM_MAX_TOKENS` | 4096 | Макс. длина ответа |
| `LLM_TEMPERATURE` | 0.3 | Температура (0 = точнее, 1 = креативнее) |
| `LLM_GPU_LAYERS` | -1 | GPU слои (-1 = все, 0 = CPU) |
| `CHUNK_SIZE` | 1500 | Размер фрагмента текста |
| `RETRIEVAL_TOP_K` | 15 | Кандидатов при поиске |
| `RERANK_TOP_K` | 8 | Финальных результатов после реранкинга |
| `API_HOST` | `0.0.0.0` | Хост REST API |
| `API_PORT` | 8000 | Порт REST API |

---

## 📄 Лицензия

[MIT](LICENSE) — используйте свободно.

---

<div align="center">

**Сделано с ❤️ и ИИ**

*Если проект полезен — поставьте ⭐*

</div>
