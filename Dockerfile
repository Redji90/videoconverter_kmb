# Multi-stage build для Hugging Face Spaces
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Копирование package файлов
COPY frontend/package*.json ./
RUN npm ci

# Копирование исходников frontend
COPY frontend/ ./

# Сборка production версии
RUN npm run build

# Stage 2: Backend + Frontend
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка Python зависимостей
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование backend кода
COPY backend/ .

# Копирование собранного frontend из Stage 1 в директорию static
COPY --from=frontend-builder /app/dist ./static

# Проверка что статика скопирована
RUN ls -la static/ || echo "Static files directory created"

# Создание директорий для моделей
RUN mkdir -p /app/models /app/huggingface-cache

# Переменные окружения
ENV PORT=7860
ENV WHISPER_CACHE_DIR=/app/models
ENV HF_HOME=/app/huggingface-cache
ENV PYTHONUNBUFFERED=1

# Открытие порта
EXPOSE 7860

# Health check (используем curl вместо requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-7860}/health || exit 1

# Запуск приложения
# Используем переменную PORT для совместимости с Spaces
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}

