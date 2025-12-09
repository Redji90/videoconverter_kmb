# Dockerfile для Hugging Face Spaces
# Порт должен быть 7860 для Spaces

FROM python:3.10-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Node.js 18 для сборки frontend
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка Python зависимостей
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Сборка frontend
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Копирование backend кода
WORKDIR /app
COPY backend/ ./backend/

# Создание директории для статики и копирование собранного frontend
RUN mkdir -p /app/static
RUN if [ -d "/app/frontend/dist" ] && [ "$(ls -A /app/frontend/dist)" ]; then \
        cp -r /app/frontend/dist/* /app/static/; \
        echo "Frontend статика скопирована в /app/static"; \
        echo "Содержимое /app/static:"; \
        ls -la /app/static/; \
        echo "Проверка index.html:"; \
        if [ -f "/app/static/index.html" ]; then \
            echo "index.html найден"; \
            head -20 /app/static/index.html; \
        else \
            echo "ОШИБКА: index.html не найден!"; \
        fi; \
    else \
        echo "Предупреждение: frontend/dist не найден или пуст"; \
        echo "Содержимое /app/frontend:"; \
        ls -la /app/frontend/; \
    fi

# Создание директорий для моделей
RUN mkdir -p /app/models /app/huggingface-cache

# Установка переменных окружения для моделей
ENV WHISPER_CACHE_DIR=/app/models
ENV HF_HOME=/app/huggingface-cache
ENV PYTHONUNBUFFERED=1

# Открытие порта для Hugging Face Spaces
EXPOSE 7860

# Запуск приложения на порту 7860
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
