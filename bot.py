import os
import sqlite3
import datetime
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    JobQueue
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
        content_for_opinion = """
            Представь, что ты очень плохой шутник и попытаешься сделать очень плохую и 
            глупую шутку над моим следующим текстом. Пусть шутки будут очень очень обидными, 
            добавь еще в конце одно из трех: "Какая жалость", "Лох", "Спасибо что позвали" стараясь подобрать по смыслу к шутке
        """
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": content_for_opinion
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


# === 1. Функция, получающая "Game of Thrones" тайтлы для каждого участника ===
async def generate_got_titles():
    # 1. Собираем список участников из БД (по сути - все, кто когда-то писал боту)
    conn = sqlite3.connect('bot_stats.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT user_id, username FROM interactions")
    users = c.fetchall()
    conn.close()

    # Если нет пользователей
    if not users:
        return "Пока нет ни одного участника, у кого есть записи в БД."

    # Сформируем список имён, уберём пустые
    # (вдруг кто-то писал без username, тогда подставим что-то вместо)
    names = []
    for user_id_val, username_val in users:
        display_name = username_val if username_val else f"ID_{user_id_val}"
        names.append(display_name)

    # 2. Готовим системное сообщение для GPT: пусть сгенерирует уникальные титулы
    # Лучше одним запросом, чтобы GPT сгенерировал список
    try:
        # Создаём текст для GPT
        # Например, передадим список имён и попросим для каждого придумать тайтл:
        prompt_for_gpt = (
            "Представь, что все эти пользователи — герои Игры Престолов. "
            "Придумай каждому эпичный уникальный титул в стиле сериала. "
            "Формат вывода: «@Имя: Титул».\n\n"
            "Список участников:\n" + "\n".join(names)
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — настоящий мейстер из Вестероса, придумываешь эпичные титулы в стиле 'Игры престолов'."
                },
                {
                    "role": "user",
                    "content": prompt_for_gpt
                }
            ]
        )
        gpt_response = response.choices[0].message.content
        return gpt_response

    except Exception as e:
        return f"Ошибка при генерации титулов: {str(e)}"

# === 2. Команда /got — чтобы можно было вручную получить титулы ===
async def got_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ограничиваем чат
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Эта команда доступна только в одной группе.")
        return

    # Запрашиваем тайтлы и отправляем
    titles_text = await generate_got_titles()
    await update.message.reply_text(titles_text)

# === 3. Периодическая задача (каждый четверг в 19:00) ===
#    Обратите внимание: дни недели в run_daily считаются с 0 (понедельник) по 6 (воскресенье).
#    Четверг = 3.
async def send_weekly_got_titles(context: ContextTypes.DEFAULT_TYPE):
    # Генерируем тайтлы
    titles_text = await generate_got_titles()
    # Отправляем в нужный чат
    await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=titles_text)

def main():
    app = Application.builder().token(TOKEN).build()

    # Добавляем хендлеры
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("chinese", chinese))
    # Команда /got для ручного запроса
    app.add_handler(CommandHandler("got", got_command))

    # При любом тексте, в котором встречается слово "мнение" (в любом регистре)
    opinion_filter = filters.TEXT & filters.Regex(r'(?i)\bмнение\b')
    app.add_handler(MessageHandler(opinion_filter, handle_opinion))

    # Настраиваем JobQueue для еженедельной отправки
    # Часовой пояс берётся тот, который на сервере (или можно задать tzinfo).
    job_queue = app.job_queue
    job_queue.run_daily(
        send_weekly_got_titles,
        time=datetime.time(hour=19, minute=0),
        days=(3,)  # 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс
    )

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
