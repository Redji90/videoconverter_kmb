# 🚀 Гайды по деплою на различные хостинги

## 🥇 1. Hugging Face Spaces (Рекомендуется)

### Подготовка

1. **Создать репозиторий на Hugging Face:**
   - Зайти на https://huggingface.co/new-space
   - Выбрать тип: Docker
   - Создать Space

2. **Создать файлы для деплоя:**

#### `app.py` (в корне репозитория)
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Подключаем статику (frontend build)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Подключаем backend API
from backend.app.main import app as backend_app
app.mount("/api", backend_app)

# Главная страница
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))
```

#### `Dockerfile` (в корне)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей backend
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Копирование кода backend
COPY backend/ /app/backend/

# Сборка frontend
COPY frontend/ /app/frontend/
WORKDIR /app/frontend
RUN apt-get update && apt-get install -y nodejs npm && \
    npm install && \
    npm run build && \
    mv dist /app/static && \
    rm -rf /app/frontend && \
    apt-get purge -y nodejs npm && \
    apt-get autoremove -y

WORKDIR /app

# Копирование app.py
COPY app.py .

# Установка переменных окружения
ENV PORT=7860
ENV WHISPER_CACHE_DIR=/app/models
ENV HF_HOME=/app/huggingface-cache

# Создание директорий для моделей
RUN mkdir -p /app/models /app/huggingface-cache

# Запуск приложения
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT}
```

#### `README.md`
```yaml
---
title: Video to Text Converter
emoji: 🎥
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Video to Text Converter

Конвертер видео в текст с использованием Whisper и speaker diarization.
```

### Деплой

```bash
# Клонировать Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# Добавить файлы
# ... скопировать файлы проекта ...

# Запушить
git add .
git commit -m "Initial commit"
git push
```

---

## 🥈 2. Fly.io

### Подготовка

1. **Установить Fly CLI:**
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

2. **Создать fly.toml:**

#### `fly.toml`
```toml
app = "your-app-name"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  WHISPER_CACHE_DIR = "/app/models"
  HF_HOME = "/app/huggingface-cache"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [services.concurrency]
    type = "connections"
    hard_limit = 25
    soft_limit = 20

  [[services.http_checks]]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
```

#### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# Frontend (build)
COPY frontend/dist ./static

# Переменные окружения
ENV WHISPER_CACHE_DIR=/app/models
ENV HF_HOME=/app/huggingface-cache

# Создание volumes для моделей (persistent storage)
RUN mkdir -p /app/models /app/huggingface-cache

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Деплой

```bash
# Логин
fly auth login

# Создать приложение
fly launch

# Создать volume для моделей (persistent storage)
fly volumes create models_data --size 10 --region iad
fly volumes create hf_cache --size 10 --region iad

# Примонтировать volumes в fly.toml:
# [mounts]
#   source="models_data"
#   destination="/app/models"
#
#   source="hf_cache"
#   destination="/app/huggingface-cache"

# Деплой
fly deploy
```

---

## 🥉 3. Railway

### Подготовка

1. **Создать `railway.json`:**
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

2. **Dockerfile** (аналогично Fly.io)

### Деплой

```bash
# Установить Railway CLI
npm i -g @railway/cli

# Логин
railway login

# Инициализация
railway init

# Добавить переменные окружения
railway variables set WHISPER_CACHE_DIR=/app/models
railway variables set HF_HOME=/app/huggingface-cache
railway variables set PORT=8000

# Деплой
railway up
```

---

## 🔧 Общие оптимизации для всех платформ

### 1. Оптимизация Dockerfile (multi-stage build)

```dockerfile
# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY backend/ .

# Копирование собранного frontend
COPY --from=frontend-builder /app/dist ./static

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Оптимизация памяти

#### Использовать base модель вместо medium:
```python
# В config.py или переменных окружения
DEFAULT_MODEL = "base"  # вместо "medium"
```

#### Lazy loading моделей:
```python
# Загружать модель только при первом использовании
# Не хранить все модели в памяти одновременно
```

### 3. Внешнее хранилище для моделей

#### Использовать Cloud Storage (S3, GCS):
```python
import boto3

def download_model_if_needed(model_name):
    cache_path = Path(WHISPER_CACHE_DIR) / f"{model_name}.pt"
    if not cache_path.exists():
        # Скачать из S3
        s3 = boto3.client('s3')
        s3.download_file('your-bucket', f'models/{model_name}.pt', str(cache_path))
```

### 4. Оптимизация frontend build

#### `vite.config.ts`:
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
})
```

---

## 📝 Переменные окружения

Создайте `.env.example`:
```env
# Пути к моделям
WHISPER_CACHE_DIR=/app/models
HF_HOME=/app/huggingface-cache

# HuggingFace токен (для diarization)
HF_TOKEN=your_token_here

# Настройки сервера
PORT=8000
USE_GPU=false

# Опционально: внешнее хранилище
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
S3_BUCKET_NAME=
```

---

## 🚨 Важные замечания

1. **Модели Whisper большие:**
   - Используйте внешнее хранилище или volumes
   - Не коммитьте модели в Git

2. **Время обработки:**
   - На бесплатных хостингах может быть медленнее
   - Рассмотрите асинхронную обработку с очередями

3. **Лимиты памяти:**
   - Используйте base модель вместо medium
   - Оптимизируйте загрузку моделей

4. **Засыпание:**
   - Настройте cron для пробуждения (Railway, Render)
   - Или используйте Fly.io (не засыпает)

---

## 🔗 Полезные ссылки

- [Hugging Face Spaces Docs](https://huggingface.co/docs/hub/spaces)
- [Fly.io Docs](https://fly.io/docs/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)


