# Используем официальный образ Python как базовый образ
FROM python:3.9-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями в рабочую директорию
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта в рабочую директорию
COPY . .

# Указывае sudo nano /etc/systemd/system/myapp.serviceм порт, который будет использовать приложение
EXPOSE 8081

# Команда для запуска приложения
CMD ["python", "bot.py"]