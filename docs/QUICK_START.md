# Быстрый старт проекта

## Предварительные требования

- **Python 3.10+** (для backend)
- **Node.js 18+** (для frontend)
- **FFmpeg** (для обработки видео)

## Установка FFmpeg

### Windows:
1. Скачайте FFmpeg с [официального сайта](https://ffmpeg.org/download.html)
2. Распакуйте архив
3. Добавьте путь к `bin` в переменную окружения `PATH`
4. Проверьте установку: `ffmpeg -version`

### Linux/Mac:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Mac
brew install ffmpeg
```

## Запуск Backend (FastAPI)

### 1. Перейдите в папку backend:
```bash
cd backend
```

### 2. Создайте виртуальное окружение (если еще не создано):
```bash
# Windows PowerShell
py -m venv venv
.\venv\Scripts\Activate.ps1

# Windows CMD
py -m venv venv
.\venv\Scripts\activate.bat

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

**Примечание для PowerShell:** Если возникает ошибка выполнения скриптов, выполните:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 4. Запустите сервер:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend будет доступен по адресу: **http://localhost:8000**

### Проверка работы backend:
- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Тестовый endpoint: http://localhost:8000/api/test

## Запуск Frontend (React + Vite)

### 1. Перейдите в папку frontend:
```bash
cd frontend
```

### 2. Установите зависимости (если еще не установлены):
```bash
npm install
```

### 3. Запустите dev сервер:
```bash
npm run dev
```

Frontend будет доступен по адресу: **http://localhost:5173**

## Запуск через Docker Compose (альтернативный способ)

Если у вас установлен Docker:

```bash
# Из корневой папки проекта
docker-compose up --build
```

Это запустит оба сервиса одновременно:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## Структура запуска

### Вариант 1: Два отдельных терминала

**Терминал 1 (Backend):**
```bash
cd backend
.\venv\Scripts\activate  # Windows
# или source venv/bin/activate  # Linux/Mac
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Терминал 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Вариант 2: PowerShell скрипт (Windows)

Создайте файл `start.ps1` в корне проекта:

```powershell
# Запуск Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\activate; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

# Запуск Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"
```

Запустите: `.\start.ps1`

## Настройка путей к моделям (опционально)

Если вы хотите использовать кастомные пути для моделей Whisper, создайте файл `backend/.env` или отредактируйте `backend/config.py`:

```python
# backend/config.py
WHISPER_CACHE_DIR = "E:\\whisper-models"  # Windows
# или
WHISPER_CACHE_DIR = "/path/to/models"     # Linux/Mac
```

## Проверка работы

1. Откройте браузер: http://localhost:5173
2. Загрузите видео файл
3. Выберите настройки (язык, модель)
4. Нажмите "Конвертировать в текст"

## Возможные проблемы

### Backend не запускается:
- Проверьте, что Python установлен: `py --version`
- Убедитесь, что виртуальное окружение активировано
- Проверьте, что все зависимости установлены: `pip list`

### Frontend не запускается:
- Проверьте, что Node.js установлен: `node --version`
- Убедитесь, что зависимости установлены: `npm install`
- Проверьте, что порт 5173 свободен

### Ошибка при обработке видео:
- Убедитесь, что FFmpeg установлен и доступен в PATH
- Проверьте формат видео файла (поддерживаются: MP4, AVI, MOV, MKV)

### CORS ошибки:
- Убедитесь, что backend запущен на порту 8000
- Проверьте настройки CORS в `backend/app/main.py`

## Остановка серверов

- **Backend**: Нажмите `Ctrl+C` в терминале с backend
- **Frontend**: Нажмите `Ctrl+C` в терминале с frontend
- **Docker Compose**: `docker-compose down`
