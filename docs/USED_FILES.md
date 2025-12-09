# Список файлов, используемых в проекте

## Backend (Python/FastAPI)

### Основные файлы приложения
- `backend/app/__init__.py` - инициализация модуля приложения
- `backend/app/main.py` - главный файл FastAPI приложения (точка входа)
- `backend/config.py` - конфигурация (пути к моделям, кэши)

### Сервисы
- `backend/app/services/__init__.py` - инициализация модуля сервисов
- `backend/app/services/video_processor.py` - обработка видео (извлечение аудио)
- `backend/app/services/speech_recognition.py` - стандартный сервис распознавания речи (Whisper)
- `backend/app/services/speech_recognition_optimized.py` - оптимизированный сервис (Faster-Whisper + Diarization)
- `backend/app/services/simple_diarization.py` - простая реализация разделения по ролям

### Конфигурация и зависимости
- `backend/requirements.txt` - Python зависимости
- `backend/Dockerfile` - Docker образ для backend

## Frontend (React/TypeScript/Vite)

### Основные файлы приложения
- `frontend/index.html` - HTML шаблон
- `frontend/src/main.tsx` - точка входа React приложения
- `frontend/src/App.tsx` - главный компонент приложения
- `frontend/src/App.css` - стили для App компонента
- `frontend/src/index.css` - глобальные стили (Tailwind CSS)

### Компоненты
- `frontend/src/components/VideoUploader.tsx` - компонент загрузки видео
- `frontend/src/components/ResultDisplay.tsx` - компонент отображения результатов

### Конфигурация
- `frontend/package.json` - зависимости и скрипты npm
- `frontend/package-lock.json` - зафиксированные версии зависимостей
- `frontend/vite.config.ts` - конфигурация Vite
- `frontend/tsconfig.json` - конфигурация TypeScript
- `frontend/tsconfig.node.json` - конфигурация TypeScript для Node.js
- `frontend/tailwind.config.js` - конфигурация Tailwind CSS
- `frontend/postcss.config.js` - конфигурация PostCSS
- `frontend/Dockerfile` - Docker образ для frontend

## Docker и развертывание
- `docker-compose.yml` - оркестрация контейнеров (backend + frontend)
- `Dockerfile` (в корне) - multi-stage build для Hugging Face Spaces

## Итого: 25 файлов

### Backend: 8 файлов
1. `backend/app/__init__.py`
2. `backend/app/main.py`
3. `backend/config.py`
4. `backend/app/services/__init__.py`
5. `backend/app/services/video_processor.py`
6. `backend/app/services/speech_recognition.py`
7. `backend/app/services/speech_recognition_optimized.py`
8. `backend/app/services/simple_diarization.py`
9. `backend/requirements.txt`
10. `backend/Dockerfile`

### Frontend: 13 файлов
1. `frontend/index.html`
2. `frontend/src/main.tsx`
3. `frontend/src/App.tsx`
4. `frontend/src/App.css`
5. `frontend/src/index.css`
6. `frontend/src/components/VideoUploader.tsx`
7. `frontend/src/components/ResultDisplay.tsx`
8. `frontend/package.json`
9. `frontend/package-lock.json`
10. `frontend/vite.config.ts`
11. `frontend/tsconfig.json`
12. `frontend/tsconfig.node.json`
13. `frontend/tailwind.config.js`
14. `frontend/postcss.config.js`
15. `frontend/Dockerfile`

### Docker: 2 файла
1. `docker-compose.yml`
2. `Dockerfile` (корневой)

---

## Файлы, которые НЕ используются в коде приложения

### Документация (все .md файлы)
- Все файлы с расширением `.md` в корне и в `backend/` - это документация

### Вспомогательные скрипты
- `backend/*.ps1` - PowerShell скрипты для настройки окружения
- `backend/check_*.py` - скрипты проверки
- `backend/download_*.py` - скрипты загрузки моделей
- `backend/test_*.py` - тестовые скрипты
- `backend/move_models_*.ps1` - скрипты перемещения моделей

### Сгенерированные файлы
- `backend/__pycache__/` - кэш Python
- `backend/app/__pycache__/` - кэш Python
- `backend/app/services/__pycache__/` - кэш Python
- `frontend/node_modules/` - зависимости npm
- `backend/venv/` - виртуальное окружение Python

---

## Примечания

1. **Конфигурационные файлы** (`config.py`, `package.json`, `requirements.txt`) критически важны для работы приложения
2. **Docker файлы** необходимы для контейнеризации и развертывания
3. **Все остальные .md файлы** - это документация и не используются в коде
4. **Скрипты .ps1 и вспомогательные .py** используются только для настройки окружения, но не в самом приложении

