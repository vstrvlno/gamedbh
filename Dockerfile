# Используем лёгкий базовый образ Python
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости без кеша
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Указываем команду запуска
# Render автоматически назначает порт, но aiogram использует polling, поэтому порт не нужен
CMD ["python", "bot.py"]
