# Настройка пути сохранения моделей Whisper

По умолчанию модели Whisper сохраняются в системный кэш:
- Windows: `C:\Users\<username>\.cache\whisper\`
- Linux/Mac: `~/.cache/whisper/`

Вы можете изменить путь сохранения на любой другой диск (например, диск E:).

## Способ 1: Через переменную окружения (Рекомендуется)

### В PowerShell (для текущей сессии):
```powershell
$env:WHISPER_CACHE_DIR="E:\whisper-models"
cd C:\prj\converter\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Постоянная установка в PowerShell:
```powershell
# Установить для текущего пользователя
[System.Environment]::SetEnvironmentVariable("WHISPER_CACHE_DIR", "E:\whisper-models", "User")

# Перезапустить PowerShell для применения изменений
```

### В CMD:
```cmd
set WHISPER_CACHE_DIR=E:\whisper-models
cd C:\prj\converter\backend
venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Постоянная установка в CMD (через системные настройки):
1. Откройте "Переменные среды" (Environment Variables)
2. Добавьте новую переменную:
   - Имя: `WHISPER_CACHE_DIR`
   - Значение: `E:\whisper-models`
3. Перезапустите терминал

## Способ 2: Через файл config.py

Откройте `backend/config.py` и измените значение:

```python
WHISPER_CACHE_DIR = "E:\\whisper-models"  # или "E:/whisper-models"
```

## Способ 3: Через .env файл

1. Создайте файл `backend/.env`:
```env
WHISPER_CACHE_DIR=E:\whisper-models
```

2. Установите python-dotenv (если еще не установлен):
```powershell
.\venv\Scripts\python.exe -m pip install python-dotenv
```

3. Обновите `main.py` для загрузки .env файла (добавьте в начало):
```python
from dotenv import load_dotenv
load_dotenv()
```

## Проверка

После установки переменной окружения, при запуске сервера вы должны увидеть:
```
Модели Whisper будут сохраняться в: E:\whisper-models
```

## Перенос существующих моделей

Если у вас уже есть модели в старом месте, вы можете их перенести:

```powershell
# Создать новую директорию
New-Item -ItemType Directory -Path "E:\whisper-models" -Force

# Скопировать модели (если они уже скачаны)
Copy-Item -Path "$env:USERPROFILE\.cache\whisper\*" -Destination "E:\whisper-models\" -Recurse -Force
```

## Примеры путей

- Windows: `E:\whisper-models` или `E:/whisper-models`
- Linux: `/mnt/e/whisper-models` или `/home/user/whisper-models`
- Mac: `/Volumes/External/whisper-models`

## Важно

- Убедитесь, что у приложения есть права на запись в указанную директорию
- Путь должен существовать или быть создаваемым
- Используйте прямые слеши `/` или двойные обратные `\\` в Windows



