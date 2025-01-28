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
    if update.effective_user.id != 270587758:  # Замените на ваш user_id
        await update.message.reply_text("❌ Доступ запрещен")
        return

    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM interactions")
    total = c.fetchone()[0]
    
    c.execute("SELECT request, COUNT(*) FROM interactions GROUP BY request ORDER BY 2 DESC LIMIT 5")
    popular = "\n".join([f"{row[0]} ({row[1]})" for row in c.fetchall()])
    
    await update.message.reply_text(f"📊 Статистика:\n\n• Всего запросов: {total}\n• Топ-5:\n{popular}")
    conn.close()

# Команда /chinese
async def chinese(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = " ".join(context.args).strip()
    if not user_text:
        await update.message.reply_text("❌ Пример: /chinese Текст вашего вопроса")
        return

    try:
        response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Отвечай в стиле китайской мудрости"},
                    {
                        "role": "user",
                        "content": user_text
                    }
    ]
)
        gpt_response = response.choices[0].message.content
        log_interaction(update.effective_user.id, update.effective_user.username, user_text, gpt_response)
        await update.message.reply_text(gpt_response)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {str(e)}")

# # Обработка обычных сообщений
# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     request = update.message.text
#     response = f"Вы написали: {request}"
#     log_interaction(update.effective_user.id, update.effective_user.username, request, response)
#     await update.message.reply_text(response)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("chinese", chinese))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
