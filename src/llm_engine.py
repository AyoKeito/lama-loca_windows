"""
LLM Engine — обёртка над LM Studio (OpenAI-совместимый API)
"""
import re
from typing import Generator

from rich.console import Console

import config

console = Console()


class LLMEngine:
    """Клиент для LM Studio локального API"""

    def __init__(self):
        self._client = None
        self._loaded = False

    def load(self) -> bool:
        from openai import OpenAI
        self._client = OpenAI(
            base_url=config.LM_STUDIO_URL,
            api_key="lm-studio",
        )
        # Проверка соединения и получение модели
        try:
            models = self._client.models.list()
            available = [m.id for m in models.data]
            if not available:
                raise RuntimeError(
                    "LM Studio запущен, но нет загруженных моделей. "
                    "Загрузите модель в LM Studio и нажмите 'Start Server'."
                )
            # Используем указанную модель или первую доступную
            if config.LM_STUDIO_MODEL and config.LM_STUDIO_MODEL in available:
                self._model_id = config.LM_STUDIO_MODEL
            else:
                self._model_id = available[0]
            self._loaded = True
            console.print(f"[green]Модель загружена: {self._model_id}[/green]")
            return True
        except Exception as e:
            raise RuntimeError(
                f"Не удалось подключиться к LM Studio ({config.LM_STUDIO_URL}).\n"
                f"Убедитесь что LM Studio запущен и сервер активен.\n"
                f"Ошибка: {e}"
            )

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def generate(self, prompt: str, max_tokens: int = None,
                 temperature: float = None) -> str:
        """Генерация текста"""
        if not self._loaded:
            self.load()

        response = self._client.chat.completions.create(
            model=self._model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or config.LLM_MAX_TOKENS,
            temperature=temperature if temperature is not None else config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
        )
        return self._strip_think(response.choices[0].message.content.strip())

    def generate_stream(self, prompt: str, max_tokens: int = None,
                        temperature: float = None) -> Generator[str, None, None]:
        """Потоковая генерация текста (для GUI), с фильтрацией <think> блоков"""
        if not self._loaded:
            self.load()

        stream = self._client.chat.completions.create(
            model=self._model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens or config.LLM_MAX_TOKENS,
            temperature=temperature if temperature is not None else config.LLM_TEMPERATURE,
            top_p=config.LLM_TOP_P,
            stream=True,
        )
        # Буфер для отлова <think>...</think> в потоке
        buffer = ""
        in_think = False
        for chunk in stream:
            token = chunk.choices[0].delta.content
            if not token:
                continue
            buffer += token
            # Ищем открывающий тег
            while True:
                if in_think:
                    end = buffer.find("</think>")
                    if end != -1:
                        buffer = buffer[end + len("</think>"):]
                        in_think = False
                    else:
                        buffer = ""  # Весь буфер — внутри think, выбрасываем
                        break
                else:
                    start = buffer.find("<think>")
                    if start != -1:
                        # Отдаём текст до тега
                        before = buffer[:start]
                        if before:
                            yield before
                        buffer = buffer[start + len("<think>"):]
                        in_think = True
                    else:
                        # Нет тега — безопасно отдавать всё кроме возможного начала тега
                        safe_len = max(0, len(buffer) - len("<think>"))
                        if safe_len > 0:
                            yield buffer[:safe_len]
                            buffer = buffer[safe_len:]
                        break
        # Остаток буфера (если не в think-блоке)
        if buffer and not in_think:
            yield buffer

    def generate_with_context(self, template: str, topic: str, context: str,
                               max_tokens: int = None, stream: bool = False):
        """Генерация с контекстом из базы знаний"""
        prompt = template.format(
            system=config.SYSTEM_PROMPT,
            topic=topic,
            context=context,
        )
        if config.LLM_DEBUG:
            console.print(f"\n[bold cyan]===== DEBUG: PROMPT SENT TO LM STUDIO =====[/bold cyan]")
            console.print(f"[cyan]Model:[/cyan] {self._model_id}")
            console.print(f"[cyan]URL:[/cyan] {config.LM_STUDIO_URL}")
            console.print(f"[cyan]Prompt ({len(prompt)} chars):[/cyan]")
            console.print(prompt[:3000] + ("..." if len(prompt) > 3000 else ""))
            console.print(f"[bold cyan]===========================================[/bold cyan]\n")
        if stream:
            return self.generate_stream(prompt, max_tokens=max_tokens)
        return self.generate(prompt, max_tokens=max_tokens)

    @staticmethod
    def _strip_think(text: str) -> str:
        """Убрать блоки <think>...</think> из ответа (reasoning-модели)"""
        # Убираем весь блок <think>...</think> включая содержимое
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return text.strip()

    def get_model_info(self) -> dict:
        """Информация о подключённой модели"""
        if not self._loaded:
            return {"status": "не подключена", "url": config.LM_STUDIO_URL}
        return {
            "status": "подключена",
            "url": config.LM_STUDIO_URL,
            "model": self._model_id,
        }
