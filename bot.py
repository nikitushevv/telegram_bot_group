import os
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI()
client.api_key = OPENAI_API_KEY

# Указываем нужный чат
ALLOWED_CHAT_ID =  -1002370287106

# Логирование в БД
def log_interaction(user_id, username, request, response):
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO interactions (user_id, username, request, response)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, request, response))
    conn.commit()
    conn.close()

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ограничиваем сам чат
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Этот бот работает только в определённой группе.")
        return

    # Ограничиваем доступ к /stats только определённому user_id
    if update.effective_user.id != 270587758:  # Замените на свой ID
        await update.message.reply_text("❌ Доступ к команде /stats запрещен")
        return

    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    
    # 1. Считаем общее количество запросов (всех пользователей)
    c.execute("SELECT COUNT(*) FROM interactions")
    total_requests = c.fetchone()[0]
    
    # 2. Считаем, сколько запросов сделал каждый пользователь
    c.execute("""
        SELECT user_id, username, COUNT(*) as cnt
        FROM interactions
        GROUP BY user_id, username
        ORDER BY cnt DESC
    """)
    rows = c.fetchall()
    
    # Формируем текст статистики по пользователям
    user_lines = []
    for user_id_val, username_val, cnt in rows:
        display_name = username_val if username_val else "unknown"
        user_lines.append(f"{display_name} ({user_id_val}): {cnt}")

    user_stats_text = "\n".join(user_lines)

    # 3. Формируем финальный текст для ответа
    stats_message = (
        f"📊 Общая статистика:\n\n"
        f"• Всего запросов: {total_requests}\n\n"
        f"Статистика по каждому пользователю:\n"
        f"{user_stats_text}"
    )

    # Отправляем сообщение
    await update.message.reply_text(stats_message)
    conn.close()

# Команда /chinese
async def chinese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ограничиваем сам чат
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Этот бот работает только в определённой группе.")
        return

    user_text = " ".join(context.args).strip()
    if not user_text:
        await update.message.reply_text("❌ Пример: /chinese Текст вашего вопроса")
        return

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Отвечай в стиле китайской мудрости"},
                {"role": "user", "content": user_text}
            ]
        )
        gpt_response = response.choices[0].message.content
        log_interaction(
            update.effective_user.id,
            update.effective_user.username,
            user_text,
            gpt_response
        )
        await update.message.reply_text(gpt_response)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")

# Хендлер на слово "мнение"
async def handle_opinion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ограничиваем сам чат
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Этот бот работает только в определённой группе.")
        return
    
    user_text = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Поделись своим мнением и проанализируй следующий текст"
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ]
        )
        gpt_response = response.choices[0].message.content
        log_interaction(
            update.effective_user.id,
            update.effective_user.username,
            user_text,
            gpt_response
        )
        await update.message.reply_text(gpt_response)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при получении мнения: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("chinese", chinese))
    
    # При любом тексте, в котором встречается слово "мнение" (в любом регистре) — handle_opinion
    opinion_filter = filters.TEXT & filters.Regex(r'(?i)\bмнение\b')
    app.add_handler(MessageHandler(opinion_filter, handle_opinion))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
