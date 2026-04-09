import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_ТУТ")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID", "ВАШ_CHAT_ID_ТУТ")

ASK_NAME, ASK_TELEGRAM, ASK_POSITION, ASK_POSITION_CUSTOM, ASK_INTERVIEW_LINK, ASK_LIKED, ASK_DOUBTS, ASK_IMPRESSION, ASK_RECOMMEND, ASK_DECISION = range(10)
POSITIONS = ["Менеджер з продажу", "Kids менеджер", "Інша позиція"]

async def start(update, context):
    context.user_data.clear()
    await update.message.reply_text(f"Привіт, {update.effective_user.first_name}!\n\nЗаповнюємо звіт по співбесіді.\nЦе займе 2-3 хвилини.\n\n*ПІБ кандидата?*", parse_mode="Markdown")
    return ASK_NAME

async def ask_name(update, context):
    context.user_data["candidate_name"] = update.message.text.strip()
    await update.message.reply_text("*Telegram кандидата* (@username або номер):", parse_mode="Markdown")
    return ASK_TELEGRAM

async def ask_telegram(update, context):
    context.user_data["candidate_telegram"] = update.message.text.strip()
    kb = [[p] for p in POSITIONS]
    await update.message.reply_text("*Позиція:*", parse_mode="Markdown", reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
    return ASK_POSITION

async def ask_position(update, context):
    text = update.message.text.strip()
    if text == "Інша позиція":
        await update.message.reply_text("Напиши назву позиції:", reply_markup=ReplyKeyboardRemove())
        return ASK_POSITION_CUSTOM
    context.user_data["position"] = text
    await update.message.reply_text("*Запис співбесіди*\nПосилання, файл або голосове. Якщо немає — напиши: немає", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    return ASK_INTERVIEW_LINK

async def ask_position_custom(update, context):
    context.user_data["position"] = update.message.text.strip()
    await update.message.reply_text("*Запис співбесіди*\nПосилання, файл або голосове. Якщо немає — напиши: немає", parse_mode="Markdown")
    return ASK_INTERVIEW_LINK

async def ask_interview_link(update, context):
    if update.message.text:
        context.user_data["interview_record"] = update.message.text.strip()
    elif update.message.voice:
        context.user_data["interview_record"] = f"[голосове file_id: {update.message.voice.file_id}]"
    elif update.message.document:
        context.user_data["interview_record"] = f"[файл: {update.message.document.file_name}]"
    else:
        context.user_data["interview_record"] = "не надано"
    await update.message.reply_text("*Що сподобалось у кандидата?*\nНапиши розгорнуто:", parse_mode="Markdown")
    return ASK_LIKED

async def ask_liked(update, context):
    context.user_data["liked"] = update.message.text.strip()
    await update.message.reply_text("*Що викликало сумніви або не підійшло?*\nНапиши розгорнуто:", parse_mode="Markdown")
    return ASK_DOUBTS

async def ask_doubts(update, context):
    context.user_data["doubts"] = update.message.text.strip()
    await update.message.reply_text("*Загальне враження від кандидата?*\nНапиши розгорнуто:", parse_mode="Markdown")
    return ASK_IMPRESSION

async def ask_impression(update, context):
    context.user_data["impression"] = update.message.text.strip()
    await update.message.reply_text("*Чи рекомендуєш кандидата далі і чому?*\nНапиши розгорнуто:", parse_mode="Markdown")
    return ASK_RECOMMEND

async def ask_recommend(update, context):
    context.user_data["recommend"] = update.message.text.strip()
    kb = [[InlineKeyboardButton("\u2705 Далі", callback_data="decision_forward")],[InlineKeyboardButton("\u26a0\ufe0f Під питанням", callback_data="decision_maybe")],[InlineKeyboardButton("\u274c Відмова", callback_data="decision_reject")]]
    await update.message.reply_text("*Фінальне рішення:*", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))
    return ASK_DECISION

async def ask_decision(update, context):
    query = update.callback_query
    await query.answer()
    decisions = {"decision_forward": "\u2705 Далі", "decision_maybe": "\u26a0\ufe0f Під питанням", "decision_reject": "\u274c Відмова"}
    context.user_data["decision"] = decisions.get(query.data, "не вказано")
    ru = f"@{query.from_user.username}" if query.from_user.username else query.from_user.first_name
    d = context.user_data
    report = (
        f"\ud83d\udccb ЗВІТ ПО СПІВБЕСІДІ\n{'─'*30}\n\n"
        f"\ud83d\udc64 Кандидат: {d.get('candidate_name','—')}\n"
        f"\ud83d\udcf1 Telegram: {d.get('candidate_telegram','—')}\n"
        f"\ud83d\udcbc Позиція: {d.get('position','—')}\n"
        f"\ud83c\udfa5 Запис: {d.get('interview_record','—')}\n\n"
        f"{'─'*30}\n\ud83d\udcac КОМЕНТАР РЕКРУТЕРА\n\n"
        f"\ud83d\udc4d Що сподобалось:\n{d.get('liked','—')}\n\n"
        f"\u26a0\ufe0f Сумніви:\n{d.get('doubts','—')}\n\n"
        f"\ud83d\udca1 Враження:\n{d.get('impression','—')}\n\n"
        f"\ud83d\udd04 Рекомендація:\n{d.get('recommend','—')}\n\n"
        f"{'─'*30}\n\ud83c\udfc1 РІШЕННЯ: {d.get('decision','—')}\n\n"
        f"{'─'*30}\n\ud83d\udc68\u200d\ud83d\udcbc Рекрутер: {ru}"
    )
    await query.edit_message_text(f"Рішення: {d['decision']}\nЗвіт відправлено керівнику!")
    try:
        await context.bot.send_message(chat_id=MANAGER_CHAT_ID, text=report)
    except Exception as e:
        logger.error(f"Помилка: {e}")
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update, context):
    context.user_data.clear()
    await update.message.reply_text("Скасовано. /start щоб почати знову.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_TELEGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_telegram)],
            ASK_POSITION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_position)],
            ASK_POSITION_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_position_custom)],
            ASK_INTERVIEW_LINK: [MessageHandler(filters.TEXT | filters.VOICE | filters.Document.ALL, ask_interview_link)],
            ASK_LIKED: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_liked)],
            ASK_DOUBTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_doubts)],
            ASK_IMPRESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_impression)],
            ASK_RECOMMEND: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_recommend)],
            ASK_DECISION: [CallbackQueryHandler(ask_decision, pattern="^decision_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
