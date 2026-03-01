from aiogram import Router, F, types, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from app.bot.states import ScreeningStates
from app.services.llm import LLMScorer
from app.services.sheets import SheetsClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = Router(name="screening_router")

llm_scorer = LLMScorer(provider=settings.llm_provider, api_key=settings.llm_api_key)
sheets_client = SheetsClient(credentials_path=settings.google_sheets_credentials_path, sheet_id=settings.google_sheet_id)
# Establish connection during import/startup
sheets_client.connect()

QUESTIONS = {
    "q1": "Вопрос 1/7\n\n"
    "Какие AI-инструменты ты используешь для разработки?\n\n"
    "Например: ChatGPT, Claude, Cursor, n8n + AI и т.д.\n\n"
    "Важно: укажи не просто список, а коротко — для чего используешь каждый инструмент.",
    "q2": "Вопрос 2/6\n\n"
    "Опиши, как выглядит твой типичный цикл работы с AI:\n"
    "первый запрос → итерации → доработка → финальная проверка.\n\n"
    "Что ты делаешь, чтобы результат был предсказуемым?",
    "q3": "Вопрос 3/6\n\n"
    "В каких типах задач AI даёт тебе наибольший буст по скорости или качеству?\n\n"
    "Приведи 1–2 конкретных примера и объясни, почему именно там.",
    "q4": "Вопрос 4/6\n\n"
    "Опиши ситуацию, когда AI выдал некорректный или вводящий в заблуждение результат.\n\n"
    "Как ты понял(а), что ответ неверный?.\т"
    "Какие шаги предпринял(а), чтобы исправить ситуацию и избежать повторения ошибки?",
    "q5": "Вопрос 5/6\n\n"
    "Когда ты получаешь размытое описание задачи (без чёткого ТЗ), "
    "как ты превращаешь его в понятный план действий с использованием AI?\n\n"
    "Кратко опиши свой подход.",
    "q6": "Пришли ссылку на решение, которое ты реализовал(а) с использованием AI.\n\n"
    "Коротко опиши:\n"
    "• в чём была задача,\n"
    "• где AI действительно сыграл ключевую роль,\n"
    "• как ты убедился(лась), что всё работает корректно.\n\n"
}

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="🚀 Начать"))
    builder.row(types.KeyboardButton(text="❓ FAQ"))
    return builder.as_markup(resize_keyboard=True)

def get_screening_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="❌ Закончить"))
    builder.row(types.KeyboardButton(text="❓ FAQ"))
    return builder.as_markup(resize_keyboard=True)

def get_refusal_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(types.KeyboardButton(text="⏭️ Пропустить"))
    builder.row(types.KeyboardButton(text="❌ Закончить"))
    return builder.as_markup(resize_keyboard=True)

@router.message(Command("cancel"))
@router.message(F.text == "❌ Закончить")
async def btn_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Собеседование и так не начато.\nЖми '🚀 Начать', если готов!", reply_markup=get_main_keyboard())
        return

    await state.clear()
    await message.answer(
        "Собеседование прервано. 🛑\nЕсли захочешь попробовать снова, нажми '🚀 Начать'.",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "❓ FAQ")
async def btn_faq(message: types.Message):
    faq_text = (
        "ℹ️ *FAQ — ответы на частые вопросы*\n\n"
        "*Сколько времени занимает скрининг?*\n"
        "В среднем 8–12 минут, если отвечать структурировано.\n\n"

        "*Можно ли отвечать кратко?*\n"
        "Да. Главное — конкретика и логика мышления, а не объём текста.\n\n"

        "*Нужно ли идеально формулировать ответы?*\n"
        "Нет. Мы оцениваем подход к работе с AI и способ рассуждения, а не стиль письма.\n\n"

        "*Что считается хорошим ответом?*\n"
        "Структура, конкретные примеры, описание процесса, объяснение проверок и критериев качества.\n\n"

        "*Что делать, если у меня нет публичного проекта?*\n"
        "Можно прислать демо или описание задачи. Главное — показать реальный опыт.\n\n"

        "*Как оцениваются ответы?*\n"
        "Мы смотрим на:\n"
        "• системность мышления,\n"
        "• умение работать с AI как инструментом,\n"
        "• инженерную адекватность и проверку результата.\n\n"

        "*Когда будет обратная связь?*\n"
        "После рассмотрения ответов команда свяжется с тобой в этом же Telegram-аккаунте.\n\n"

        "Если готов(а) — нажимай «Начать» 🚀"
    )
    await message.answer(faq_text, parse_mode="Markdown")

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    """Greets the user and explains the format."""
    await state.clear()
    welcome_text = (
        "Привет! 👋 Я бот для AI-first скрининга.\n"
        "Мы ищем людей, которые умеют мыслить через ИИ: декомпозировать задачи, правильно ставить запросы и автоматизировать рутину.\n\n"
        "Как всё будет устроено:\n"
        "1. Сначала немного познакомимся.\n"
        "2. Затем я задам тебе 5 вопросов о том, как ты подходишь к задачам и работаешь с ИИ.\n"
        "3. Также я попрошу ссылку на проект или решение, которое ты сделал с использованием ИИ.\n"
        "4. После этого команда изучит ответы, и я вернусь к тебе с обратной связью на этот же Telegram-аккаунт.\n\n"
        "Это займёт примерно 8–12 минут.\n\n"
        "Как тебя зовут? Пожалуйста, введи свои **Имя и Фамилию**:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_screening_keyboard())
    await state.set_state(ScreeningStates.waiting_for_name)

@router.message(F.text == "🚀 Начать")
async def btn_start(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

@router.message(ScreeningStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    full_name = message.text or ""
    if len(full_name.split()) < 2:
        await message.answer("Пожалуйста, введи Имя и Фамилию (не менее двух слов).")
        return
    
    await state.update_data({"full_name": full_name})
    await message.answer(f"Приятно познакомиться, {full_name.split()[0]}! Начнем.\n\n{QUESTIONS['q1']}")
    await state.set_state(ScreeningStates.waiting_for_q2)

async def handle_answer_and_proceed(message: types.Message, state: FSMContext, next_state, next_question_key: str, answer_key: str):
    user_text = message.text or ""

    if user_text == "⏭️ Пропустить":
        await state.update_data({answer_key: "Пропущено пользователем"})
        await message.answer(QUESTIONS[next_question_key], reply_markup=get_screening_keyboard())
        await state.set_state(next_state)
        return
    
    # Validation step
    validation = await llm_scorer.validate_answer(user_text)
    
    if not validation["is_valid"]:
        if validation.get("is_refusal"):
             await message.answer(
                 "Хочешь пропустить этот вопрос?",
                 reply_markup=get_refusal_keyboard()
             )
        else:
            await message.answer(validation.get("error_message") or "Пожалуйста, ответь более развернуто.")
        return

    if validation.get("warning"):
        await message.answer(f"⚠️ {validation['warning']}")

    # User answered properly, update state
    await state.update_data({answer_key: user_text})
    await message.answer(QUESTIONS[next_question_key], reply_markup=get_screening_keyboard())
    await state.set_state(next_state)

@router.message(ScreeningStates.waiting_for_q2)
async def process_q1(message: types.Message, state: FSMContext):
    await handle_answer_and_proceed(message, state, ScreeningStates.waiting_for_q3, "q2", "answer_1")

@router.message(ScreeningStates.waiting_for_q3)
async def process_q2(message: types.Message, state: FSMContext):
    await handle_answer_and_proceed(message, state, ScreeningStates.waiting_for_q4, "q3", "answer_2")

@router.message(ScreeningStates.waiting_for_q4)
async def process_q3(message: types.Message, state: FSMContext):
    await handle_answer_and_proceed(message, state, ScreeningStates.waiting_for_q5, "q4", "answer_3")

@router.message(ScreeningStates.waiting_for_q5)
async def process_q4(message: types.Message, state: FSMContext):
    await handle_answer_and_proceed(message, state, ScreeningStates.waiting_for_q6, "q5", "answer_4")

@router.message(ScreeningStates.waiting_for_q6)
async def process_q5(message: types.Message, state: FSMContext):
    await handle_answer_and_proceed(message, state, ScreeningStates.waiting_for_link, "q6", "answer_5")

@router.message(ScreeningStates.waiting_for_link)
async def process_q6_link(message: types.Message, state: FSMContext, bot: Bot):
    user_text = message.text or ""

    if user_text == "⏭️ Пропустить":
        user_text = "Ссылка пропущена"
    else:
        validation = await llm_scorer.validate_url(user_text)
        if not validation["is_valid"]:
            await message.answer(f"❌ {validation.get('error_message') or 'Некорректная ссылка.'}\nЕсли у тебя нет ссылки — можешь ввести /cancel или попробовать ещё раз.")
            return

    await state.update_data({"answer_6_link": user_text})
    user_data = await state.get_data()

    final_message = (
        "Спасибо за ответы 🙌\n\n"
        "Я зафиксировал всю информацию и передал её на оценку.\n"
        "Мы проанализируем твои ответы и проект, после чего вернёмся с обратной связью в этом же Telegram-аккаунте.\n\n"
        "Обычно это занимает немного времени. "
        "Если ты подходишь нам по результатам скрининга — свяжемся с тобой для следующего шага.\n\n"
        "Хорошего дня 🚀"
    )

    await message.answer(final_message, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    answers_list = [
        user_data.get("answer_1", ""),
        user_data.get("answer_2", ""),
        user_data.get("answer_3", ""),
        user_data.get("answer_4", ""),
        user_data.get("answer_5", "")
    ]
    project_link = user_data.get("answer_6_link", "")

    # Score candidates
    try:
        evaluation = await llm_scorer.score_candidate(answers_list, project_link)
    except Exception as e:
        logger.error(f"Scoring error: {e}")
        await message.answer("Произошла ошибка при анализе твоих ответов. Мы сохранили их и рассмотрим вручную.")
        await state.clear()
        return

    # Save to sheets
    try:
        logger.info(f"Saving results to Google Sheets for user {message.from_user.id}")
        sheets_client.append_row(
            user_id=message.from_user.id,
            full_name=user_data.get("full_name", "N/A"),
            username=message.from_user.username,
            score=evaluation.get("score", 0),
            is_hot=evaluation.get("is_hot", False),
            eval_reasons=evaluation.get("eval_reasons", ""),
            answers=answers_list,
            link=project_link
        )
    except Exception as e:
        logger.error(f"Failed to save to Google Sheets: {e}", exc_info=True)


    # Notify admin if hot
    if evaluation.get('is_hot') and settings.notification_chat_id:
        user_info = f"@{message.from_user.username}" if message.from_user.username else f"[ссылка](tg://user?id={message.from_user.id})"
        admin_text = (
            f"🔥 **Новый Hot-кандидат!** 🔥\n\n"
            f"Кандидат: {user_data.get('full_name', 'N/A')}\n"
            f"Профиль: {user_info}\n"
            f"Балл: {evaluation['score']}/30\n"
            f"Обоснование: {evaluation['eval_reasons']}\n"
            f"Ссылка на проект: {project_link}"
        )
        try:
            logger.info(f"Sending hot candidate notification for user {message.from_user.id}")
            await bot.send_message(chat_id=settings.notification_chat_id, text=admin_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Could not notify admin: {e}", exc_info=True)

    logger.info(f"Screening completed for user {message.from_user.id}")
    await state.clear()


@router.message()
async def fallback_handler(message: types.Message):
    """Catch-all for any messages that don't match a state or command."""
    await message.answer("Пожалуйста, используй кнопки или команду /start для навигации.", reply_markup=get_main_keyboard())
