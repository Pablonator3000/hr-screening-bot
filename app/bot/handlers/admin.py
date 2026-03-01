from aiogram import Router, F, types
from aiogram.filters import Command
import logging
from app.config import settings
from app.services.sheets import SheetsClient

logger = logging.getLogger(__name__)
router = Router(name="admin_router")

# Initialize sheets client
sheets_client = SheetsClient(
    credentials_path=settings.google_sheets_credentials_path, 
    sheet_id=settings.google_sheet_id
)
sheets_client.connect()

@router.message(Command("admin"))
async def admin_dashboard(message: types.Message):
    """
    Показывает статистику бота и топ кандидатов из Google Sheets.
    """
    logger.info(f"Admin dashboard requested by user {message.from_user.id}")
    if str(message.from_user.id) not in settings.admin_chat_id:
         logger.warning(f"Unauthorized admin access attempt by user {message.from_user.id}")
         await message.answer("У вас нет прав для просмотра этой страницы.")
         return

    try:
        stats = sheets_client.get_stats()
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении статистики. Попробуйте позже.")
        return
    
    if not stats or stats.get("total_screened") == 0:
        await message.answer("📊 *Админ-панель*\n\nДанных пока нет. Начните скрининг!")
        return

    top_text = ""
    for i, cand in enumerate(stats.get("top_candidates", []), 1):
        name = cand.get("Full Name", "N/A")
        score = cand.get("Score", 0)
        top_text += f"{i}. {name} — {score}/30\n"

    stats_text = (
        "📊 *Админ-панель*\n\n"
        f"Всего прошли скрининг: **{stats['total_screened']}**\n"
        f"Средний балл: **{stats['avg_score']}/30**\n\n"
        "🔥 **Топ-3 кандидата:**\n"
        f"{top_text}"
    )
    await message.answer(stats_text, parse_mode="Markdown")
