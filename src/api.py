"""
REST API для интеграции с n8n и другими внешними сервисами.
Запускается на порту API_PORT (по умолчанию 8000) параллельно с Gradio GUI.

Эндпоинты:
  GET  /api/health            — проверка состояния
  GET  /api/stats             — статистика базы знаний
  POST /api/chat              — вопрос-ответ (RAG)
  POST /api/generate          — генерация документа (отчёт, конспект, эссе и т.д.)
  POST /api/presentation      — генерация структуры презентации
  POST /api/index             — индексировать все книги из папки books/
  POST /api/books/upload      — загрузить и проиндексировать файл книги
  DELETE /api/knowledge-base  — очистить базу знаний
"""
import os
import shutil
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

import config

app = FastAPI(
    title="Lama Loca API",
    description="REST API для Study AI Assistant — интеграция с n8n и другими сервисами",
    version="1.0.0",
)

# Фабричные функции из main.py для ленивой инициализации
_init_kb_fn = None
_init_llm_fn = None
_doc_gen = None
_pres_gen = None


def set_globals(init_kb_fn, init_llm_fn, doc_gen, pres_gen):
    """Вызывается из main.py. Передаёт фабричные функции init_kb/init_llm."""
    global _init_kb_fn, _init_llm_fn, _doc_gen, _pres_gen
    _init_kb_fn = init_kb_fn
    _init_llm_fn = init_llm_fn
    _doc_gen = doc_gen
    _pres_gen = pres_gen


def _get_kb():
    if _init_kb_fn is None:
        raise HTTPException(status_code=503, detail="API не инициализирован. Запустите main.py.")
    try:
        return _init_kb_fn()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


def _get_llm():
    if _init_llm_fn is None:
        raise HTTPException(status_code=503, detail="API не инициализирован. Запустите main.py.")
    try:
        return _init_llm_fn()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ======================================================================
# Схемы запросов / ответов
# ======================================================================

class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    sources_used: bool


class GenerateRequest(BaseModel):
    topic: str
    doc_type: str = "report"
    format: str = "md"


DOC_TYPE_CHOICES = ["report", "summary", "essay", "analysis", "exam_prep"]
FORMAT_CHOICES = ["md", "docx", "both"]


class GenerateResponse(BaseModel):
    text: str
    files: List[str]


class PresentationRequest(BaseModel):
    topic: str
    save: bool = True


class PresentationResponse(BaseModel):
    structure: str
    file: Optional[str] = None


class IndexResponse(BaseModel):
    result: str
    total_books: int
    total_chunks: int


class StatsResponse(BaseModel):
    total_books: int
    total_chunks: int
    books: List[str]
    model_loaded: bool
    model_path: str
    model_exists: bool


# ======================================================================
# Эндпоинты
# ======================================================================

@app.get("/api/health")
def health():
    """Проверка состояния сервиса."""
    return {
        "status": "ok",
        "model_exists": os.path.exists(config.LLM_MODEL_PATH),
        "model_loaded": _llm.is_loaded if _llm else False,
    }


@app.get("/api/stats", response_model=StatsResponse)
def stats():
    """Статистика базы знаний и состояние модели."""
    kb = _get_kb()
    s = kb.stats()
    return StatsResponse(
        total_books=s["total_books"],
        total_chunks=s["total_chunks"],
        books=s["books"],
        model_loaded=_llm.is_loaded if _llm else False,
        model_path=config.LLM_MODEL_PATH,
        model_exists=os.path.exists(config.LLM_MODEL_PATH),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Задать вопрос по загруженным книгам.

    Пример тела запроса для n8n:
    ```json
    { "message": "Что такое фотосинтез?" }
    ```
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Поле message не может быть пустым")

    kb = _get_kb()
    llm = _get_llm()

    context = kb.search(req.message)
    sources_used = not context.startswith("База знаний пуста")

    template = config.PROMPTS["qa"]
    answer = llm.generate_with_context(template, req.message, context)

    return ChatResponse(answer=answer, sources_used=sources_used)


@app.post("/api/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """
    Сгенерировать учебный документ по теме.

    Поле `doc_type`: report | summary | essay | analysis | exam_prep
    Поле `format`: md | docx | both

    Пример для n8n:
    ```json
    { "topic": "Термодинамика", "doc_type": "report", "format": "md" }
    ```
    """
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Поле topic не может быть пустым")
    if req.doc_type not in DOC_TYPE_CHOICES:
        raise HTTPException(status_code=400, detail=f"doc_type должен быть одним из: {DOC_TYPE_CHOICES}")
    if req.format not in FORMAT_CHOICES:
        raise HTTPException(status_code=400, detail=f"format должен быть одним из: {FORMAT_CHOICES}")

    kb = _get_kb()
    llm = _get_llm()

    context = kb.search(req.topic)
    template = config.PROMPTS[req.doc_type]
    text = llm.generate_with_context(template, req.topic, context)

    files = _doc_gen.generate(text, req.topic, req.doc_type, req.format)
    filenames = [os.path.basename(f) for f in files]

    return GenerateResponse(text=text, files=filenames)


@app.post("/api/presentation", response_model=PresentationResponse)
def presentation(req: PresentationRequest):
    """
    Сгенерировать презентацию PowerPoint.

    Пример для n8n:
    ```json
    { "topic": "Квантовая механика", "save": true }
    ```
    """
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="Поле topic не может быть пустым")

    kb = _get_kb()
    llm = _get_llm()

    context = kb.search(req.topic)
    text = llm.generate_with_context(config.PROMPTS["presentation"], req.topic, context)

    file_path = None
    filename = None
    if req.save:
        file_path = _pres_gen.generate(text, req.topic)
        filename = os.path.basename(file_path)

    return PresentationResponse(structure=text, file=filename)


@app.post("/api/index", response_model=IndexResponse)
def index_books():
    """
    Проиндексировать все книги из папки books/.
    Уже проиндексированные книги пропускаются.
    """
    kb = _get_kb()
    result = kb.index_all_books()
    s = kb.stats()
    return IndexResponse(result=result, total_books=s["total_books"], total_chunks=s["total_chunks"])


@app.post("/api/books/upload")
def upload_book(file: UploadFile = File(...)):
    """
    Загрузить файл книги и сразу проиндексировать его.
    Поддерживаемые форматы: PDF, TXT, EPUB, DOCX, MD, FB2, HTML.

    В n8n используйте тип Binary в HTTP Request node.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in config.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат {ext}. Поддерживаются: {config.SUPPORTED_FORMATS}"
        )

    dest = os.path.join(config.BOOKS_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    kb = _get_kb()
    result = kb.add_book(dest)
    s = kb.stats()

    return {"result": result, "total_books": s["total_books"], "total_chunks": s["total_chunks"]}


@app.delete("/api/knowledge-base")
def clear_knowledge_base():
    """Полностью очистить векторную базу знаний."""
    kb = _get_kb()
    result = kb.clear()
    return {"result": result}


@app.get("/api/files")
def list_files():
    """Список сгенерированных документов в папке output/."""
    files = []
    if os.path.exists(config.OUTPUT_DIR):
        for fname in sorted(os.listdir(config.OUTPUT_DIR), reverse=True):
            fpath = os.path.join(config.OUTPUT_DIR, fname)
            size = os.path.getsize(fpath)
            files.append({"name": fname, "size_bytes": size})
    return {"files": files}


@app.get("/api/files/{filename}")
def download_file(filename: str):
    """Скачать сгенерированный документ по имени файла."""
    # Защита от path traversal
    safe_name = os.path.basename(filename)
    fpath = os.path.join(config.OUTPUT_DIR, safe_name)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(fpath, filename=safe_name)
