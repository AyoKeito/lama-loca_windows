# CLAUDE.md

Этот файл содержит инструкции для Claude Code (claude.ai/code) при работе с данным репозиторием.

## Обзор

Lama Loca — полностью офлайн локальный ИИ-ассистент для учёбы. Пользователи загружают книги (PDF/EPUB/DOCX/TXT/FB2/HTML/MD), система индексирует их в ChromaDB, а затем отвечает на вопросы и генерирует учебные документы (отчёты, эссе, презентации, конспекты) с помощью локальной GGUF-модели через llama-cpp-python.

Дополнительно работает REST API (FastAPI, порт 8000) для интеграции с n8n и другими сервисами автоматизации.

## Установка и запуск

**Linux / macOS:**
```bash
chmod +x setup.sh && ./setup.sh
source venv/bin/activate
python main.py
```

**Windows:**
```cmd
setup.bat
venv\Scripts\activate
python main.py
```

- GUI: `http://localhost:7860`
- REST API + Swagger: `http://localhost:8000/docs`

**GPU ускорение (NVIDIA CUDA):**
```bash
pip install llama-cpp-python --force-reinstall --no-cache-dir \
    -C cmake.args="-DGGML_CUDA=ON"
```

## Требование: модель LLM

Приложению нужен файл GGUF по пути `models/model.gguf`. Без него LLM-функции завершаются с `FileNotFoundError`. Скачать пример:
```bash
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2.5-14B-Instruct-GGUF \
    qwen2.5-14b-instruct-q4_k_m.gguf \
    --local-dir models/ --local-dir-use-symlinks False
# Linux/macOS:
mv models/qwen2.5-14b-instruct-q4_k_m.gguf models/model.gguf
# Windows:
move models\qwen2.5-14b-instruct-q4_k_m.gguf models\model.gguf
```

## Архитектура

RAG-пайплайн: файлы книг → извлечение текста → чанкинг (1500 символов, overlap 300) → эмбеддинги E5-Large → ChromaDB. При запросе: эмбеддинг запроса → поиск top-15 кандидатов → Cross-Encoder реранкер → top-8 чанков → вставка в промпт → генерация LLM.

Параллельно с Gradio GUI запускается FastAPI REST API в фоновом потоке (daemon). Оба компонента используют одни и те же ленивые инстансы `KnowledgeBase` и `LLMEngine` через фабричные функции `init_kb()` / `init_llm()`.

### Ключевые модули

- **[config.py](config.py)** — все константы конфигурации. Единственный источник истины для путей, параметров модели, чанкинга и шаблонов промптов (`PROMPTS` dict: `report`, `presentation`, `summary`, `essay`, `qa`, `analysis`, `exam_prep`). Также содержит `API_HOST` и `API_PORT`.

- **[main.py](main.py)** — Gradio GUI + запуск REST API. Ленивая инициализация `LLMEngine` и `KnowledgeBase` как глобальных объектов. Запускает FastAPI-сервер в фоновом потоке (`daemon=True`) через `_start_api_server()`.

- **[src/api.py](src/api.py)** — FastAPI REST API. `set_globals(init_kb_fn, init_llm_fn, doc_gen, pres_gen)` передаёт фабричные функции из `main.py` — объекты инициализируются по требованию при первом запросе. Эндпоинты: `/api/health`, `/api/stats`, `/api/chat`, `/api/generate`, `/api/presentation`, `/api/index`, `/api/books/upload`, `/api/knowledge-base` (DELETE), `/api/files`.

- **[src/llm_engine.py](src/llm_engine.py)** — `LLMEngine` оборачивает llama-cpp-python. Ключевой метод: `generate_with_context(template, topic, context, stream=False)` форматирует промпт по шаблонам из config и вызывает модель. Поддерживается стриминг для чата.

- **[src/knowledge_base.py](src/knowledge_base.py)** — `KnowledgeBase` обрабатывает индексацию и поиск. Загрузчики файлов — функции уровня модуля в словаре `LOADERS`. E5-Large требует префикс `"passage: "` для документов и `"query: "` для запросов. `Reranker` лениво загружает Cross-Encoder.

- **[src/document_generator.py](src/document_generator.py)** — `DocumentGenerator` сохраняет вывод LLM как DOCX (Times New Roman, академическое форматирование) или Markdown в `output/`.

- **[src/presentation_generator.py](src/presentation_generator.py)** — `PresentationGenerator` разбирает вывод LLM по маркерам `СЛАЙД N:` для построения PPTX-слайдов. Если маркеры не найдены — фолбэк на разбиение по абзацам.

## Рабочие директории (в .gitignore)

| Директория | Назначение |
|-----------|---------|
| `books/` | Исходные книги для индексации |
| `models/` | GGUF-файл модели (`model.gguf`) |
| `output/` | Сгенерированные DOCX/PPTX/MD файлы |
| `data/chromadb/` | Персистентная векторная БД ChromaDB |

## Конфигурация

Все параметры в [config.py](config.py):

| Параметр | По умолчанию | Примечание |
|---------|---------|-------|
| `LLM_GPU_LAYERS` | `-1` | `0` для только CPU |
| `LLM_CONTEXT_SIZE` | `32768` | Уменьшить при нехватке памяти |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-large` | Скачивается с HuggingFace при первом запуске |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-12-v2` | Скачивается с HuggingFace при первом запуске |
| `USE_RERANKER` | `True` | `False` — отключить реранкинг |
| `API_HOST` | `0.0.0.0` | Хост REST API |
| `API_PORT` | `8000` | Порт REST API |

## Формат промптов

Все промпты используют формат ChatML (`<|im_start|>system ... <|im_end|>`), соответствующий моделям Qwen2.5 Instruct. Стоп-токены: `["<|im_end|>", "<|end|>", "</s>", "<|eot_id|>"]`.

## Совместимость с Windows

- Используйте `setup.bat` вместо `setup.sh`
- Активация venv: `venv\Scripts\activate` (не `source venv/bin/activate`)
- `load_fb2_file` в `knowledge_base.py` использует `load_text_file()` для поддержки нескольких кодировок (utf-8, cp1251, latin-1, cp866) — важно для русскоязычных файлов на Windows
- `os.path.join` используется везде — пути корректно работают на Windows
