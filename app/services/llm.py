from typing import Dict, Any, List

import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class LLMScorer:
    def __init__(self, provider: str, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    async def _call_llm(self, initial_prompt: str, user_data: str, json_mode: bool = True) -> str:
        """Internal method to call the chosen LLM provider."""
        if not self.client:
            logger.error("LLM client not initialized.")
            return "{}"
            
        try:
            logger.info(f"Calling LLM provider: {self.provider}")
            kwargs = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": initial_prompt},
                    {"role": "user", "content": user_data}
                ],
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.client.chat.completions.create(**kwargs)
            logger.info("LLM call successful.")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return "{}"

    async def validate_answer(self, user_text: str) -> Dict[str, Any]:
        """
        Validates a candidate's answer using LLM.
        """
        prompt = (
            "Ты — ассистент по валидации ответов кандидатов. Проверь текст на:\n"
            "1. Отказ отвечать (например: 'не знаю', 'пропущу', 'не хочу', '-') -> is_refusal: true\n"
            "2. Мусор/спам (бессмысленный набор букв, повторы символов 'aaaaa', 'qwerty') -> is_valid: false\n"
            "3. Слишком короткий или пустой ответ (< 15-20 символов) -> is_valid: false\n"
            "4. Избыток 'воды' (> 1000 символов) -> warning: 'Слишком длинно'\n\n"
            "Верни JSON: { 'is_valid': bool, 'error_message': str, 'is_refusal': bool, 'warning': str }"
        )
        
        result = await self._call_llm(prompt, user_text)
        try:
            return json.loads(result)
        except:
            return {"is_valid": True, "error_message": None, "is_refusal": False, "warning": None}

    async def validate_url(self, url: str) -> Dict[str, Any]:
        """
        Validates a project URL using LLM (to catch clever spam/fake links).
        """
        prompt = (
            "Проверь, является ли это корректной ссылкой на проект (github, notion, сайт и т.д.).\n"
            "Не пропускай: localhost, 127.0.0.1, файловые пути, бессмысленные домены типа http://a.\n\n"
            "Верни JSON: { 'is_valid': bool, 'error_message': str }"
        )
        
        result = await self._call_llm(prompt, url)
        try:
            return json.loads(result)
        except:
            return {"is_valid": True, "error_message": None}

    async def score_candidate(self, answers: List[str], project_link: str) -> Dict[str, Any]:
        """
        Evaluates candidate's answers using an LLM.
        """
        system_prompt = system_prompt = '''Ты — технический лид и эксперт по AI-first разработке, оценивающий кандидата.
Тебе предоставлены ответы кандидата на вопросы о его рабочем процессе, а также ссылка на реализованный им проект.

Твоя задача — строго и объективно оценить кандидата.

Оцени по 3 критериям (целые числа от 0 до 10):

1. Tool Awareness:
Оцени знание современных AI-инструментов, понимание их ролей, ограничений и уместности применения.
0–3: поверхностное знание, без аргументации
4–6: знает несколько инструментов, но выбор не всегда обоснован
7–8: осознанно выбирает инструменты под задачи
9–10: демонстрирует системное понимание экосистемы и trade-offs

2. Process Efficiency:
Оцени наличие воспроизводимого workflow, умение итерировать и структурировать работу с AI.
0–3: хаотичное использование
4–6: есть процесс, но без явных критериев качества
7–8: структурированный цикл работы
9–10: чёткая методология с проверками и self-review

3. Critical Thinking:
Оцени способность замечать ошибки AI, проверять результат, учитывать edge cases.
0–3: доверяет AI без проверки
4–6: проверяет, но поверхностно
7–8: осознанно тестирует и валидирует
9–10: демонстрирует инженерную строгость и критичность

Обязательно:
- Используй только целые числа.
- score должен быть равен сумме трёх критериев.
- Не добавляй никакого текста вне JSON.

Верни ответ СТРОГО в формате JSON:

{
  "tool_awareness": <0-10>,
  "process_efficiency": <0-10>,
  "critical_thinking": <0-10>,
  "score": <сумма_трёх_критериев>,
  "eval_reasons": "Подробный разбор по каждому критерию:\n
Tool Awareness (X/10): объясни, какие признаки из ответов повлияли на оценку.\n
Process Efficiency (X/10): укажи, есть ли системность, итерации, критерии качества.\n
Critical Thinking (X/10): оцени проверку ошибок, работу с галлюцинациями и edge cases.\n
\n
Сильные стороны: перечисли конкретные сильные сигналы.\n
Слабые стороны: перечисли конкретные пробелы или риски.\n
Итог: краткий общий вывод о зрелости AI-first мышления.",
  "is_hot": <true если score >= 24 И нет ни одного критерия ниже 7, иначе false>
}'''

        user_content = f"Ответы: {json.dumps(answers, ensure_ascii=False)}\nСсылка на проект: {project_link}"
        
        result_str = await self._call_llm(system_prompt, user_content)
        
        try:
            return json.loads(result_str)
        except json.JSONDecodeError:
            return {
                "score": 0,
                "eval_reasons": "Ошибка парсинга ответа от LLM",
                "is_hot": False
            }


