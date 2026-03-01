import re
from urllib.parse import urlparse
from typing import Tuple, Optional, Dict

class InputValidator:
    """
    Handles 'hard' validation of user inputs before LLM scoring.
    """

    REFUSAL_TRIGGERS = [
        "не хочу", "пропущу", "не знаю", "без ответа", "-", "скип", "pass", "no answer", "skip"
    ]

    SPAM_PATTERNS = [
        r"(.)\1{4,}",  # 5+ repeating characters (aaaaa)
        r"(qwerty|asdfgh|zxcvbn|йцукен|фывапр|ячсмить)", # Keyboard rows
    ]

    @staticmethod
    def validate_answer(text: str) -> Dict[str, any]:
        """
        Validates a typical text answer.
        Returns: {
            'is_valid': bool,
            'error_message': str,
            'is_refusal': bool,
            'warning': str
        }
        """
        text = text.strip()
        lower_text = text.lower()

        # 1. Refusal check
        if any(trigger in lower_text for trigger in InputValidator.REFUSAL_TRIGGERS) or lower_text in ["-", ".", "pass"]:
            return {
                "is_valid": False,
                "error_message": "Вы выбрали пропустить вопрос или не давать ответ.",
                "is_refusal": True,
                "warning": None
            }

        # 2. Too short
        if len(text) < 20:
            return {
                "is_valid": False,
                "error_message": "Похоже, ответ слишком короткий. Можешь добавить 1–2 предложения?",
                "is_refusal": False,
                "warning": None
            }

        # 3. Spam check
        for pattern in InputValidator.SPAM_PATTERNS:
            if re.search(pattern, lower_text):
                return {
                    "is_valid": False,
                    "error_message": "Похоже на случайный текст или повтор символов. Можешь ответить осмысленно в 2–4 предложениях?",
                    "is_refusal": False,
                    "warning": None
                }
        
        # Low entropy check (e.g. 'abcabcabcabcabc')
        if len(text) > 30 and len(set(lower_text)) < 6:
            return {
                "is_valid": False,
                "error_message": "Ответ выглядит очень однообразно. Пожалуйста, напиши полноценное предложение.",
                "is_refusal": False,
                "warning": None
            }

        warning = None
        if len(text) > 1500:
            warning = "Твой ответ очень подробный! Было бы здорово, если бы ты смог(ла) выделить 3 основных тезиса (буллета), но я принимаю его и так."

        return {
            "is_valid": True,
            "error_message": None,
            "is_refusal": False,
            "warning": warning
        }

    @staticmethod
    def validate_url(url: str) -> Dict[str, any]:
        """
        Validates the project link.
        """
        url = url.strip()
        
        if " " in url:
            return {"is_valid": False, "error_message": "Ссылка не должна содержать пробелы."}

        if len(url) < 10:
            return {"is_valid": False, "error_message": "Ссылка слишком короткая. Пожалуйста, пришли полный URL."}

        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ["http", "https"]:
            return {"is_valid": False, "error_message": "Ссылка должна начинаться с http:// или https://"}

        if not parsed.netloc or "." not in parsed.netloc or len(parsed.netloc) < 4:
            return {"is_valid": False, "error_message": "Пожалуйста, введи корректный домен (например, github.com)."}

        forbidden = ["localhost", "127.0.0.1"]
        if any(f in parsed.netloc for f in forbidden) or parsed.scheme == "file":
            return {"is_valid": False, "error_message": "Локальные ссылки или файловые пути не принимаются. Пришли ссылку на веб-ресурс."}

        return {"is_valid": True, "error_message": None}
