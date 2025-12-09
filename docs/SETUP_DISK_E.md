# Настройка сохранения моделей на диск E

## Для моделей Whisper (транскрипция):

```powershell
# Для текущей сессии
$env:WHISPER_CACHE_DIR="E:\whisper-models"

# Или постоянная установка
[System.Environment]::SetEnvironmentVariable("WHISPER_CACHE_DIR", "E:\whisper-models", "User")
```

## Для моделей Diarization (разделение по ролям):

```powershell
# Для текущей сессии
$env:HF_HOME="E:\huggingface-cache"

# Или постоянная установка
[System.Environment]::SetEnvironmentVariable("HF_HOME", "E:\huggingface-cache", "User")
```

## Или через config.py:

Откройте `backend/config.py` и измените:

```python
WHISPER_CACHE_DIR = "E:\\whisper-models"
HF_HOME = "E:\\huggingface-cache"
```

## Полная настройка (все модели на диск E):

```powershell
# Установить обе переменные
$env:WHISPER_CACHE_DIR="E:\whisper-models"
$env:HF_HOME="E:\huggingface-cache"

# Перезапустить сервер
cd C:\prj\converter\backend
.\run_server.ps1
```

## Проверка:

После перезапуска сервера вы должны увидеть:
```
✓ Модели Whisper будут сохраняться в: E:\whisper-models
✓ Модели HuggingFace (diarization) будут сохраняться в: E:\huggingface-cache
```

## Перенос существующих моделей:

Если модели уже скачаны в старые места:

```powershell
# Создать директории
New-Item -ItemType Directory -Path "E:\whisper-models" -Force
New-Item -ItemType Directory -Path "E:\huggingface-cache" -Force

# Скопировать модели Whisper (если есть)
if (Test-Path "$env:USERPROFILE\.cache\whisper") {
    Copy-Item -Path "$env:USERPROFILE\.cache\whisper\*" -Destination "E:\whisper-models\" -Recurse -Force
}

# Скопировать модели HuggingFace (если есть)
if (Test-Path "$env:USERPROFILE\.cache\huggingface") {
    Copy-Item -Path "$env:USERPROFILE\.cache\huggingface\*" -Destination "E:\huggingface-cache\" -Recurse -Force
}
```

## Важно:

- Убедитесь, что у приложения есть права на запись в эти директории
- После установки переменных перезапустите сервер
- Модели будут скачиваться в новые места при следующем использовании



