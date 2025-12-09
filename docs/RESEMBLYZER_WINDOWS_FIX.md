# Решение проблемы установки Resemblyzer на Windows

## Проблема

При установке Resemblyzer возникает ошибка:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

Это происходит из-за зависимости `webrtcvad`, которую нужно скомпилировать.

## Решения

### Решение 1: Установить Microsoft C++ Build Tools (рекомендуется)

1. Скачайте Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Установите, выбрав:
   - "Desktop development with C++"
   - "MSVC v143 - VS 2022 C++ x64/x86 build tools"
3. После установки перезапустите PowerShell
4. Попробуйте установить снова:
   ```powershell
   pip install resemblyzer librosa soundfile
   ```

### Решение 2: Использовать предкомпилированный wheel

Попробуйте установить предкомпилированную версию webrtcvad:

```powershell
# Попробуйте установить webrtcvad отдельно с принудительной установкой
pip install webrtcvad-wheels

# Или используйте альтернативный репозиторий
pip install --only-binary :all: webrtcvad

# Затем установите resemblyzer
pip install resemblyzer librosa soundfile
```

### Решение 3: Установить без webrtcvad (не рекомендуется)

webrtcvad используется для Voice Activity Detection (VAD). Если не критично, можно попробовать обойти:

```powershell
# Установите остальные зависимости
pip install librosa soundfile typing

# Установите resemblyzer без зависимостей
pip install --no-deps resemblyzer

# Или отредактируйте requirements и уберите webrtcvad
# Но это может привести к проблемам в работе
```

### Решение 4: Использовать альтернативу через pipwin

```powershell
# Установите pipwin (менеджер предкомпилированных пакетов для Windows)
pip install pipwin

# Попробуйте установить webrtcvad через pipwin
pipwin install webrtcvad

# Затем установите resemblyzer
pip install resemblyzer librosa soundfile
```

### Решение 5: Использовать Docker (если доступно)

Если у вас установлен Docker, можно использовать Linux-окружение:

```dockerfile
FROM python:3.10
RUN pip install resemblyzer librosa soundfile
```

## Быстрое решение (самое простое)

Если нужен быстрый результат, установите Build Tools:

1. Откройте: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
2. Скачайте "Build Tools for Visual Studio 2022"
3. Запустите установщик
4. Выберите "Desktop development with C++"
5. Установите
6. Перезапустите PowerShell
7. Установите пакеты:
   ```powershell
   pip install resemblyzer librosa soundfile
   ```

## Альтернатива: Использовать другую библиотеку

Если установка Resemblyzer проблематична, рассмотрите альтернативы:

### Вариант 1: Продолжить с Pyannote (через токен)
- Примите условия для segmentation-3.0
- Используйте токен HuggingFace
- Это самое надежное решение

### Вариант 2: SpeechBrain (может быть проще)
```powershell
pip install speechbrain
```

### Вариант 3: Использовать только Whisper без diarization
- Whisper уже установлен
- Можно использовать без разделения по ролям
- Просто отключите опцию diarization в интерфейсе

## Проверка установки

После установки проверьте:

```powershell
python -c "from resemblyzer import VoiceEncoder; print('✓ Resemblyzer установлен!')"
```

Если ошибка - значит не установлен.

## Рекомендация

Для Windows лучше всего:
1. Установить Build Tools (если есть время)
2. Или использовать Pyannote с токеном (более надежно)
3. Или использовать только Whisper без diarization (самый простой вариант)


