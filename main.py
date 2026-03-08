#!/usr/bin/env python3
"""
Study AI Assistant — GUI приложение на Gradio + REST API для n8n
"""
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
import config
from src.llm_engine import LLMEngine
from src.knowledge_base import KnowledgeBase
from src.document_generator import DocumentGenerator
from src.presentation_generator import PresentationGenerator

# ======================================================================
# Глобальные объекты
# ======================================================================
llm: LLMEngine = None
kb: KnowledgeBase = None
doc_gen = DocumentGenerator()
pres_gen = PresentationGenerator()
_init_lock = threading.Lock()


def init_kb():
    global kb
    if kb is None:
        kb = KnowledgeBase()
    return kb


def init_llm():
    global llm
    if llm is None:
        llm = LLMEngine()
        llm.load()
    return llm


def _start_api_server():
    """Запустить FastAPI сервер в фоновом потоке."""
    import uvicorn
    from src.api import app as api_app, set_globals
    set_globals(init_kb, init_llm, doc_gen, pres_gen)
    uvicorn.run(
        api_app,
        host=config.API_HOST,
        port=config.API_PORT,
        log_level="warning",
    )


# ======================================================================
# Обработчики GUI
# ======================================================================

def on_index_books():
    """Индексация всех книг"""
    try:
        k = init_kb()
        result = k.index_all_books()
        stats = k.stats()
        summary = (
            f"{result}\n\n"
            f"📊 Статистика:\n"
            f"  Книг: {stats['total_books']}\n"
            f"  Фрагментов: {stats['total_chunks']}\n"
        )
        if stats['books']:
            summary += "  Книги: " + ", ".join(stats['books'])
        return summary
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_add_book(files):
    """Добавить загруженные книги"""
    if not files:
        return "Выберите файлы для загрузки"

    try:
        k = init_kb()
        results = []

        import shutil
        for file in files:
            # Gradio 6: FileData object with .path; older: .name or plain string
            file_path = getattr(file, 'path', None) or getattr(file, 'name', None) or file
            filename = os.path.basename(file_path)
            dest = os.path.join(config.BOOKS_DIR, filename)
            shutil.copy2(file_path, dest)

            result = k.add_book(dest)
            results.append(result)

        stats = k.stats()
        return "\n".join(results) + f"\n\n📊 Всего: {stats['total_books']} книг, {stats['total_chunks']} фрагментов"
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_clear_kb():
    """Очистить базу знаний"""
    try:
        k = init_kb()
        return k.clear()
    except Exception as e:
        return f"❌ Ошибка: {e}"


def on_get_stats():
    """Получить статистику"""
    try:
        k = init_kb()
        stats = k.stats()
        text = (
            f"📚 Книг проиндексировано: {stats['total_books']}\n"
            f"📄 Фрагментов текста: {stats['total_chunks']}\n"
        )
        if stats['books']:
            text += "\n📖 Книги:\n"
            for b in stats['books']:
                text += f"  • {b}\n"
        else:
            text += "\n⚠️ Книги не добавлены. Загрузите книги через вкладку «Книги»."
        return text
    except Exception as e:
        return f"❌ Ошибка: {e}"


def generate_document(topic: str, doc_type: str, fmt: str):
    """Генерация документа любого типа"""
    if not topic.strip():
        return "Введите тему", None

    try:
        k = init_kb()
        l = init_llm()

        # Выбираем шаблон
        type_map = {
            "Отчёт": "report",
            "Конспект": "summary",
            "Эссе": "essay",
            "Анализ": "analysis",
            "Подготовка к экзамену": "exam_prep",
        }
        template_key = type_map.get(doc_type, "report")
        template = config.PROMPTS[template_key]

        # Поиск контекста
        context = k.search(topic)

        # Генерация
        text = l.generate_with_context(template, topic, context)

        # Сохранение
        fmt_map = {"Оба (DOCX + MD)": "both", "DOCX": "docx", "Markdown": "md"}
        out_fmt = fmt_map.get(fmt, "both")

        doc_type_ru = {
            "Отчёт": "отчёт", "Конспект": "конспект", "Эссе": "эссе",
            "Анализ": "анализ", "Подготовка к экзамену": "экзамен"
        }

        files = doc_gen.generate(text, topic, doc_type_ru.get(doc_type, "документ"), out_fmt)

        file_list = "\n".join([f"📁 {os.path.basename(f)}" for f in files])
        return text, f"✅ Сохранено:\n{file_list}\n\nПапка: {config.OUTPUT_DIR}"

    except FileNotFoundError as e:
        return str(e), "❌ Модель не найдена. Скачайте модель (см. вкладку «Настройки»)"
    except Exception as e:
        return f"❌ Ошибка: {e}", f"❌ {e}"


def generate_presentation(topic: str):
    """Генерация презентации"""
    if not topic.strip():
        return "Введите тему", None

    try:
        k = init_kb()
        l = init_llm()

        context = k.search(topic)
        text = l.generate_with_context(config.PROMPTS["presentation"], topic, context)
        filepath = pres_gen.generate(text, topic)

        return text, f"✅ Презентация сохранена:\n📁 {os.path.basename(filepath)}\n\nПапка: {config.OUTPUT_DIR}"

    except FileNotFoundError as e:
        return str(e), "❌ Модель не найдена"
    except Exception as e:
        return f"❌ Ошибка: {e}", f"❌ {e}"


def chat_respond(message: str, history: list):
    """Интерактивный чат"""
    if not message.strip():
        return "", history

    try:
        k = init_kb()
        l = init_llm()

        context = k.search(message)
        template = config.PROMPTS["qa"]

        # Потоковая генерация
        response = ""
        for token in l.generate_with_context(template, message, context, stream=True):
            response += token
            yield history + [{"role": "user", "content": message}, {"role": "assistant", "content": response}]

    except FileNotFoundError:
        yield history + [{"role": "user", "content": message}, {"role": "assistant", "content": "❌ Модель не найдена. Скачайте модель и укажите путь в config.py"}]
    except Exception as e:
        yield history + [{"role": "user", "content": message}, {"role": "assistant", "content": f"❌ Ошибка: {e}"}]


def get_lm_studio_status():
    """Проверить статус LM Studio"""
    import urllib.request
    try:
        r = urllib.request.urlopen(f"{config.LM_STUDIO_URL}/models", timeout=3)
        import json
        data = json.loads(r.read())
        models = [m["id"] for m in data.get("data", [])]
        if models:
            return f"✅ LM Studio подключён\nМодели: {', '.join(models)}"
        return "⚠️ LM Studio запущен, но нет загруженных моделей"
    except Exception as e:
        return f"❌ LM Studio недоступен ({config.LM_STUDIO_URL})\n{e}"


def save_settings(lm_url, lm_model, max_tokens, temperature, top_p,
                  chunk_size, chunk_overlap, retrieval_top_k, rerank_top_k,
                  emb_use_lm_studio, emb_lm_studio_model, emb_hf_model):
    """Применить и сохранить настройки"""
    config.LM_STUDIO_URL = lm_url.strip()
    config.LM_STUDIO_MODEL = lm_model.strip()
    config.LLM_MAX_TOKENS = int(max_tokens)
    config.LLM_TEMPERATURE = float(temperature)
    config.LLM_TOP_P = float(top_p)
    config.CHUNK_SIZE = int(chunk_size)
    config.CHUNK_OVERLAP = int(chunk_overlap)
    config.RETRIEVAL_TOP_K = int(retrieval_top_k)
    config.RERANK_TOP_K = int(rerank_top_k)
    config.EMBEDDING_USE_LM_STUDIO = emb_use_lm_studio
    config.EMBEDDING_LM_STUDIO_MODEL = emb_lm_studio_model.strip()
    config.EMBEDDING_MODEL = emb_hf_model.strip()
    config.save_settings()
    # Сбросить LLM и KB чтобы переподключиться с новыми настройками
    global llm, kb
    llm = None
    kb = None
    return "✅ Настройки сохранены. LLM и база знаний переподключатся при следующем запросе."


def list_output_files():
    """Список файлов в output/"""
    files = []
    if os.path.exists(config.OUTPUT_DIR):
        for f in sorted(os.listdir(config.OUTPUT_DIR), reverse=True):
            path = os.path.join(config.OUTPUT_DIR, f)
            size = os.path.getsize(path)
            size_str = f"{size / 1024:.1f} KB" if size < 1024 * 1024 else f"{size / (1024 * 1024):.1f} MB"
            files.append(f"📄 {f} ({size_str})")
    if not files:
        return "Пока нет созданных документов"
    return "\n".join(files)


def get_output_files_for_download():
    """Получить файлы для скачивания"""
    files = []
    if os.path.exists(config.OUTPUT_DIR):
        for f in sorted(os.listdir(config.OUTPUT_DIR), reverse=True):
            files.append(os.path.join(config.OUTPUT_DIR, f))
    return files


# ======================================================================
# GUI
# ======================================================================

custom_css = """
    .gradio-container {
        max-width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .app-header {
        padding: 10px 20px;
        border-bottom: 1px solid #2d2d2d;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .app-header h1 {
        font-size: 1.3em;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    """


def create_gui():
    """Создать интерфейс Gradio"""

    with gr.Blocks(title="Lama Loca — Study AI", fill_height=True) as app:

        # --- Шапка ---
        gr.HTML("""
        <div class="app-header">
            <h1>📚 Lama Loca</h1>
            <span style="color:#94a3b8; font-size:0.9em;">Локальный ИИ-ассистент для учёбы</span>
        </div>
        """)

        with gr.Row(elem_classes=["main-layout"]):

            # ========== ЛЕВАЯ КОЛОНКА: история ==========
            with gr.Column(scale=0, min_width=200, elem_classes=["sidebar-left"]):
                gr.Markdown("**История чата**", elem_id="history-label")
                chat_clear = gr.Button("+ Новый чат", variant="secondary", size="sm")
                gr.HTML("<hr style='margin:8px 0; border-color:#e2e8f0;'>")
                kb_info = gr.Markdown("*База знаний:*\nНет данных", elem_id="kb-info")
                kb_refresh_btn = gr.Button("Обновить", size="sm", variant="secondary")

            # ========== ЦЕНТРАЛЬНАЯ КОЛОНКА: чат ==========
            with gr.Column(scale=3, elem_classes=["chat-center"]):
                chatbot = gr.Chatbot(
                    height=500,
                    show_label=False,
                    elem_classes=["chatbot-wrap"],
                    render_markdown=True,
                )
                with gr.Row(equal_height=True):
                    chat_input = gr.Textbox(
                        placeholder="Введите вопрос по вашим книгам... (Enter — отправить, Shift+Enter — новая строка)",
                        show_label=False,
                        lines=2,
                        max_lines=6,
                        scale=9,
                        container=False,
                    )
                    chat_send = gr.Button("Отправить", variant="primary", scale=1, min_width=100)

            # ========== ПРАВАЯ КОЛОНКА: функции ==========
            with gr.Column(scale=1, min_width=340, elem_classes=["sidebar-right"]):
                with gr.Tabs():

                    # --- Вкладка: Документы ---
                    with gr.TabItem("📝 Документы"):
                        doc_topic = gr.Textbox(
                            label="Тема",
                            placeholder="Введите тему...",
                            lines=2,
                        )
                        doc_type = gr.Dropdown(
                            choices=["Отчёт", "Конспект", "Эссе", "Анализ", "Подготовка к экзамену"],
                            value="Отчёт",
                            label="Тип",
                        )
                        doc_format = gr.Dropdown(
                            choices=["Оба (DOCX + MD)", "DOCX", "Markdown"],
                            value="Оба (DOCX + MD)",
                            label="Формат",
                        )
                        doc_generate_btn = gr.Button("Создать документ", variant="primary")
                        doc_status = gr.Textbox(label="Статус", lines=2, interactive=False)
                        doc_output = gr.Textbox(label="Текст", lines=15, interactive=False)

                        doc_generate_btn.click(
                            generate_document,
                            inputs=[doc_topic, doc_type, doc_format],
                            outputs=[doc_output, doc_status],
                        )

                    # --- Вкладка: Презентации ---
                    with gr.TabItem("📊 Презентации"):
                        pres_topic = gr.Textbox(
                            label="Тема",
                            placeholder="Введите тему...",
                            lines=2,
                        )
                        pres_generate_btn = gr.Button("Создать презентацию", variant="primary")
                        pres_status = gr.Textbox(label="Статус", lines=2, interactive=False)
                        pres_output = gr.Textbox(label="Структура", lines=15, interactive=False)

                        pres_generate_btn.click(
                            generate_presentation,
                            inputs=[pres_topic],
                            outputs=[pres_output, pres_status],
                        )

                    # --- Вкладка: Книги ---
                    with gr.TabItem("📖 Книги"):
                        book_upload = gr.File(
                            label="Добавить книги",
                            file_count="multiple",
                            file_types=[".pdf", ".txt", ".epub", ".docx", ".md", ".fb2", ".html"],
                        )
                        book_upload_btn = gr.Button("Загрузить и индексировать", variant="primary")
                        gr.HTML("<hr style='margin:8px 0;'>")
                        book_index_btn = gr.Button("Индексировать папку books/", variant="secondary")
                        book_stats_btn = gr.Button("Показать статистику")
                        book_clear_btn = gr.Button("Очистить базу", variant="stop")
                        book_output = gr.Textbox(label="Результат", lines=8, interactive=False)

                        book_upload_btn.click(on_add_book, inputs=[book_upload], outputs=[book_output]).then(on_get_stats, outputs=[kb_info])
                        book_index_btn.click(on_index_books, outputs=[book_output]).then(on_get_stats, outputs=[kb_info])
                        book_stats_btn.click(on_get_stats, outputs=[book_output])
                        book_clear_btn.click(on_clear_kb, outputs=[book_output]).then(on_get_stats, outputs=[kb_info])

                    # --- Вкладка: Файлы ---
                    with gr.TabItem("📁 Файлы"):
                        files_refresh_btn = gr.Button("Обновить список")
                        files_list = gr.Textbox(label="Созданные документы", lines=15, value=list_output_files, interactive=False)
                        gr.Markdown(f"Папка: `{config.OUTPUT_DIR}`")
                        files_refresh_btn.click(list_output_files, outputs=[files_list])

                    # --- Вкладка: Настройки ---
                    with gr.TabItem("⚙️ Настройки"):
                        gr.Markdown("**LM Studio — генерация**")
                        s_lm_url = gr.Textbox(label="URL", value=config.LM_STUDIO_URL)
                        s_lm_model = gr.Textbox(
                            label="Модель LLM (пусто = первая доступная)",
                            value=config.LM_STUDIO_MODEL,
                            placeholder="например: qwen2.5-14b-instruct",
                        )
                        with gr.Row():
                            s_check_btn = gr.Button("Проверить соединение", variant="secondary")
                        s_status = gr.Textbox(label="Статус LM Studio", lines=2, interactive=False)
                        s_check_btn.click(get_lm_studio_status, outputs=[s_status])

                        gr.Markdown("**Параметры генерации**")
                        s_max_tokens = gr.Number(
                            label="Max tokens (ограничение длины ответа)",
                            value=config.LLM_MAX_TOKENS,
                            precision=0,
                            minimum=256,
                            maximum=32768,
                        )
                        s_temperature = gr.Slider(
                            label="Temperature (0=точно, 1=креативно)",
                            minimum=0.0, maximum=2.0, step=0.05,
                            value=config.LLM_TEMPERATURE,
                        )
                        s_top_p = gr.Slider(
                            label="Top P",
                            minimum=0.0, maximum=1.0, step=0.05,
                            value=config.LLM_TOP_P,
                        )

                        gr.Markdown("**Эмбеддинги**")
                        s_emb_use_lm_studio = gr.Checkbox(
                            label="Использовать LM Studio для эмбеддингов (быстро, без локальной модели)",
                            value=config.EMBEDDING_USE_LM_STUDIO,
                        )
                        s_emb_lm_studio_model = gr.Textbox(
                            label="Embedding-модель в LM Studio (пусто = первая доступная)",
                            value=config.EMBEDDING_LM_STUDIO_MODEL,
                            placeholder="например: nomic-embed-text",
                        )
                        s_emb_hf_model = gr.Textbox(
                            label="HuggingFace embedding-модель (если не LM Studio)",
                            value=config.EMBEDDING_MODEL,
                            placeholder="intfloat/multilingual-e5-large",
                        )
                        gr.Markdown(
                            "_Внимание: при смене модели эмбеддингов необходимо переиндексировать книги — "
                            "векторы несовместимы между разными моделями._",
                        )

                        gr.Markdown("**Параметры векторизации**")
                        with gr.Row():
                            s_chunk_size = gr.Number(
                                label="Размер чанка (символов)",
                                value=config.CHUNK_SIZE,
                                precision=0,
                                minimum=200,
                                maximum=8000,
                            )
                            s_chunk_overlap = gr.Number(
                                label="Перекрытие чанков",
                                value=config.CHUNK_OVERLAP,
                                precision=0,
                                minimum=0,
                                maximum=2000,
                            )
                        with gr.Row():
                            s_retrieval_top_k = gr.Number(
                                label="Кандидатов при поиске (retrieval_top_k)",
                                value=config.RETRIEVAL_TOP_K,
                                precision=0,
                                minimum=1,
                                maximum=50,
                            )
                            s_rerank_top_k = gr.Number(
                                label="Финальных чанков в промпт (rerank_top_k)",
                                value=config.RERANK_TOP_K,
                                precision=0,
                                minimum=1,
                                maximum=20,
                            )
                        gr.Markdown(
                            "_Чем меньше `rerank_top_k` — тем короче промпт и быстрее ответ. "
                            "При смене размера чанка нужна переиндексация._"
                        )

                        gr.Markdown(
                            f"**Система**\n"
                            f"- Реранкер: `{config.RERANKER_MODEL}`\n"
                            f"- Книги: `{config.BOOKS_DIR}`\n"
                            f"- REST API: `http://localhost:{config.API_PORT}/docs`"
                        )

                        s_save_btn = gr.Button("Сохранить настройки", variant="primary")
                        s_save_status = gr.Textbox(label="", lines=1, interactive=False)
                        s_save_btn.click(
                            save_settings,
                            inputs=[
                                s_lm_url, s_lm_model, s_max_tokens, s_temperature, s_top_p,
                                s_chunk_size, s_chunk_overlap, s_retrieval_top_k, s_rerank_top_k,
                                s_emb_use_lm_studio, s_emb_lm_studio_model, s_emb_hf_model,
                            ],
                            outputs=[s_save_status],
                        )

        # ========== Привязка событий чата ==========
        chat_send.click(
            chat_respond,
            inputs=[chat_input, chatbot],
            outputs=[chatbot],
        ).then(lambda: "", outputs=[chat_input])

        chat_input.submit(
            chat_respond,
            inputs=[chat_input, chatbot],
            outputs=[chatbot],
        ).then(lambda: "", outputs=[chat_input])

        chat_clear.click(lambda: [], outputs=[chatbot])
        kb_refresh_btn.click(on_get_stats, outputs=[kb_info])

        # Загрузить статистику при старте
        app.load(on_get_stats, outputs=[kb_info])

    return app


# ======================================================================
# Entry point
# ======================================================================

if __name__ == "__main__":
    os.makedirs(config.BOOKS_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.MODELS_DIR, exist_ok=True)
    os.makedirs(config.DATA_DIR, exist_ok=True)

    print("=" * 60)
    print("  Study AI Assistant")
    print("  Zapusk GUI + REST API...")
    print("=" * 60)

    # Запускаем REST API в фоне
    api_thread = threading.Thread(target=_start_api_server, daemon=True)
    api_thread.start()
    print(f"  REST API: http://{config.API_HOST}:{config.API_PORT}/docs")

    app = create_gui()
    app.launch(
        server_port=config.GUI_PORT,
        share=config.GUI_SHARE,
        inbrowser=True,
        css=custom_css,
        theme=gr.themes.Soft(
            primary_hue="violet",
            secondary_hue="indigo",
            neutral_hue="gray",
        ),
    )
