# Telegram Bot (для одной группы)

Это телеграм-бот, который:
- Работает **только** в одном чате (группе).
- Предоставляет команду `/stats` (с ограничением по `user_id`).
- Предоставляет команду `/chinese` (ответы в стиле китайской мудрости).
- Реагирует на слово «мнение», обрабатывая его с помощью OpenAI.
- **Раз в неделю** (по четвергам в 19:00) или по запросу (команда `/got`) генерирует каждому участнику «тайтл в стиле Игры престолов» посредством OpenAI.
- Ведёт журнал взаимодействий (логирование запросов и ответов) в локальную базу `SQLite`.

---

## Содержание

1. [Технологии](#технологии)  
2. [Установка](#установка)  
3. [Настройка окружения](#настройка-окружения)  
4. [Запуск](#запуск)  
5. [Функционал бота](#функционал-бота)  
6. [Запуск на отдельном сервере](#запуск-на-отдельном-сервере)  
7. [Пример .env файла](#пример-env-файла)  
8. [Список команд для BotFather](#список-команд-для-botfather)

---

## Технологии

- [Python 3.9+](https://www.python.org/)
- [python-telegram-bot (20.3)](https://github.com/python-telegram-bot/python-telegram-bot)
- [OpenAI API](https://github.com/openai/openai-python)
- [SQLite3](https://www.sqlite.org/index.html)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## Установка

1. **Склонируйте репозиторий** (или скопируйте файлы в нужную директорию):
   ```bash
   git clone https://github.com/your-repo/telegram-bot.git
    ```
2. **Перейдите в папку проекта:**
   ```bash
   cd telegram-bot
    ```
3. **(Опционально) Создайте и активируйте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # Или на Windows: venv\Scripts\activate
    ```
4. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
    ```
## Настройка окружения
В корне проекта должен быть файл `.env`, содержащий переменные окружения:

- `TELEGRAM_BOT_TOKEN` — токен вашего телеграм-бота, выданный BotFather.
- `OPENAI_API_KEY` — ключ доступа к OpenAI API (ChatGPT).\

Другие настройки (например, `ALLOWED_CHAT_ID`) указываются напрямую в коде `bot.py`, либо могут также читаться из `.env` при необходимости.

## Запуск
После установки зависимостей и настройки .env выполните:
   ```bash
    python bot.py
 ```
В консоли должно появиться сообщение:
   ```bash
    Бот запущен...
 ```
 Бот начнёт обрабатывать обновления от Telegram.

## Функционал бота

1. **Ограничение по чату**\
Бот работает только в одной группе (ID чата хранится в переменной `ALLOWED_CHAT_ID`).\
При попытке написать боту в другом чате бот уведомит, что не поддерживает работу вне заданной группы.

2. **Логирование в БД**\
При каждом взаимодействии (запрос/ответ) бот записывает данные в SQLite-базу `bot_stats.db` (таблица `interactions`).

3. **Команда `/stats`**
- Доступна только пользователю с определённым `user_id` (указан в `bot.py`).
- Выводит статистику:
    - Общее количество запросов.
    - Количество запросов каждого пользователя, сгруппированное по `user_id` и `username`.

4. **Команда `/chinese`**
- Принимает аргумент (например, /chinese Как стать мудрым?) и отвечает «в стиле китайской мудрости», используя OpenAI API.
- Логирует запрос/ответ в БД.

5. **Слово «мнение»**
- Любое сообщение, содержащее `мнение` (в любом регистре), бот обрабатывает через OpenAI: «поделись мнением и проанализируй текст».
- Результат отправляется обратно в группу и логируется в БД.

6. **Генерация тайтлов из Игры престолов**
- Команда `/got`: в любой момент по запросу бот собирает список участников из БД и генерирует каждому «тайтл в стиле Игры престолов» через OpenAI, затем отправляет в чат.
- Раз в неделю (четверг в 19:00) бот автоматически выполняет ту же операцию, отправляя результат в чат.

## Запуск на отдельном сервере
1. **Cкопируйте файлы** проекта на ваш сервер (Linux/Windows/MacOS).
2. **Установите зависимости** (см. пункт «[Установка](#установка)»).
3. **Настройте** `.env` (см. пункт «[Настройка окружения](#настройка-окружения)»).
4. **Запустите бота**:
    ```bash
    python bot.py
    ```
5. (Опционально) Настройте сервис (Systemd, Supervisor и т. д.), чтобы бот запускался в фоновом режиме и перезапускался в случае сбоев.

## Пример `.env` файла
```dotenv
TELEGRAM_BOT_TOKEN=1234567:AAAAAAA-XXXXXXXXXXXXXXXXXXXXXX
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXX
```
**Внимание**: никогда не коммитьте реальные токены в публичные репозитории!

## Список команд для BotFather
Чтобы при вводе «/» в телеграме появлялись подсказки к командам, в BotFather можно настроить:
```dotenv
stats - Показать статистику по боту
chinese - Ответ в стиле китайской мудрости
got - Сгенерировать тайтлы из Игры престолов
```
## 
Автор: Никита Тугушев \
Контакты: tugushevnikita@yandex.ru
