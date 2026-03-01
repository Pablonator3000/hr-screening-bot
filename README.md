# AI-First HR Screening Bot 🚀

Телеграм-бот для автоматизации первичного отбора кандидатов на основе их "AI-first" мышления. Бот опрашивает кандидата, оценивает его ответы с помощью нейросети (DeepSeek) и сохраняет результаты в Google Таблицы.

## 🌟 Основные возможности

- **Умный скрининг:** 5 вопросов, направленных на выявление навыков работы с ИИ, критического мышления и эффективности процессов.
- **Оценка через LLM (DeepSeek):** Автоматический скоринг по 3 критериям (Tool Awareness, Process Efficiency, Critical Thinking).
- **Валидация на базе ИИ:** Защита от спама, пустых ответов и некорректных ссылок.
- **Интеграция с Google Sheets:** Все ответы, баллы и ссылки на профиль кандидата сохраняются в реальном времени.
- **Уведомления об "Hot" кандидатах:** Мгновенные алерты в админский чат, если кандидат набрал высокий балл.
- **Админ-панель:** Просмотр статистики и топ-3 кандидатов прямо в боте.
- **Docker-ready:** Полная поддержка контейнеризации для быстрого развертывания.

## 🛠 Технологический стек

- **Язык:** Python 3.11
- **Фреймворк:** [Aiogram 3.x](https://docs.aiogram.dev/) (Telegram Bot API)
- **API:** [FastAPI](https://fastapi.tiangolo.com/) (для вебхуков)
- **LLM:** [DeepSeek API](https://api.deepseek.com/) (OpenAI-compatible)
- **База данных:** Google Sheets (через Gspread)
- **Контейнеризация:** Docker & Docker Compose

## 🚀 Быстрый старт

### 1. Подготовка
- Создайте бота в [@BotFather](https://t.me/BotFather) и получите токен.
- Получите API-ключ в [DeepSeek](https://platform.deepseek.com/).
- Настройте Google Service Account и скачайте файл `google_credentials.json` ([Инструкция](https://docs.gspread.org/en/v6.1.2/oauth2.html#for-bots-using-service-account)).
- Создайте Google Таблицу и дайте доступ (Editor) имейлу из сервисного аккаунта.

### 2. Настройка окружения
Создайте файл `.env` в корне проекта на основе примера:
```env
TG_BOT_TOKEN=ваш_токен_бота
LLM_API_KEY=ваш_ключ_deepseek
LLM_PROVIDER=openai
GOOGLE_SHEETS_CREDENTIALS_PATH=./google_credentials.json
GOOGLE_SHEET_ID=ID_вашей_таблицы
ADMIN_CHAT_ID=["id1", "id2"]
NOTIFICATION_CHAT_ID=id_чата_для_уведомлений
WEBHOOK_URL=  # Оставьте пустым для режима Long Polling
```

### 3. Запуск через Docker (рекомендуется)
```bash
docker-compose up --build -d
```

### 4. Локальный запуск
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запустите бота:
   ```bash
   python app/main.py
   ```

## 📊 Структура проекта

- `app/bot/` — Логика телеграм-бота (хендлеры, состояния, клавиатуры).
- `app/services/` — Внешние интеграции (LLM, Google Sheets).
- `app/config.py` — Конфигурация через Pydantic Settings.
- `app/main.py` — Точка входа (FastAPI + lifespan для бота).

## 🛡 Безопасность
- Файлы `.env` и `google_credentials.json` добавлены в `.gitignore` и `.dockerignore`.
- В Docker-compose ключи монтируются через разделы `volumes`, не попадая в образ.
