# Инструкция по установке и запуску

## Предварительные требования

### 1. Установка Python
- Python 3.10 или выше
- Скачать с [python.org](https://www.python.org/downloads/)

### 2. Установка Node.js
- Node.js 18 или выше
- Скачать с [nodejs.org](https://nodejs.org/)

### 3. Установка FFmpeg

#### Windows:
```powershell
# Используя Chocolatey
choco install ffmpeg

# Или скачать вручную с https://ffmpeg.org/download.html
# Добавить в PATH
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

---

## Установка Backend

```bash
# Перейти в директорию backend
cd backend

# Создать виртуальное окружение (рекомендуется)
python -m venv venv

# Активировать виртуальное окружение
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Если ошибка политики выполнения:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Windows CMD:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Примечание: Whisper автоматически скачает модель при первом использовании
```

---

## Установка Frontend

```bash
# Перейти в директорию frontend
cd frontend

# Установить зависимости
npm install
```

---

## Запуск приложения

### Вариант 1: Ручной запуск

#### Терминал 1 - Backend:
```powershell
# PowerShell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

```bash
# CMD или Bash
cd backend
venv\Scripts\activate  # Windows CMD
# source venv/bin/activate  # Linux/macOS
uvicorn app.main:app --reload --port 8000
```

#### Терминал 2 - Frontend:
```bash
cd frontend
npm run dev
```

Приложение будет доступно по адресу: http://localhost:5173

### Вариант 2: Docker (скоро)

---

## Проверка работы

1. Откройте http://localhost:5173 в браузере
2. Загрузите видео файл
3. Выберите настройки (язык, модель)
4. Нажмите "Конвертировать в текст"
5. Дождитесь результата

---

## Устранение проблем

### Ошибка: "FFmpeg not found"
- Убедитесь, что FFmpeg установлен и добавлен в PATH
- Проверьте: `ffmpeg -version`

### Ошибка: "Out of memory"
- Используйте меньшую модель Whisper (tiny или base)
- Закройте другие приложения

### Ошибка: "Model download failed"
- Проверьте интернет-соединение
- Whisper скачивает модели при первом использовании
- Модели сохраняются в `~/.cache/whisper/`

### Медленная обработка
- Используйте GPU для ускорения (требует CUDA)
- Или используйте меньшую модель (tiny/base)

---

## Производительность моделей Whisper

| Модель | Размер | Скорость (CPU) | Скорость (GPU) | Память |
|--------|--------|----------------|----------------|--------|
| tiny   | 39 MB  | ~16x           | ~32x           | ~1 GB  |
| base   | 74 MB  | ~10x           | ~16x           | ~1 GB  |
| small  | 244 MB | ~4x            | ~6x            | ~2 GB  |
| medium | 769 MB | ~2x            | ~5x            | ~5 GB  |
| large  | 1550 MB| 1x             | ~2x            | ~10 GB |

Рекомендуется начинать с модели **base** для баланса скорости и качества.

