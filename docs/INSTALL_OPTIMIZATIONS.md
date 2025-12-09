# Установка оптимизаций для распознавания речи

## 1. Установка Faster-Whisper (ускорение 4-5x)

### Базовая установка:
```powershell
cd C:\prj\converter\backend
.\venv\Scripts\python.exe -m pip install faster-whisper
```

### С поддержкой GPU (если есть NVIDIA GPU):
```powershell
# Установите CUDA Toolkit сначала: https://developer.nvidia.com/cuda-downloads
.\venv\Scripts\python.exe -m pip install faster-whisper
```

После установки перезапустите backend сервер.

---

## 2. Установка WhisperX (для разделения по ролям)

### Шаг 1: Установка WhisperX
```powershell
cd C:\prj\converter\backend
.\venv\Scripts\python.exe -m pip install whisperx
```

### Шаг 2: Получение токена HuggingFace (для моделей diarization)

1. Зарегистрируйтесь на https://huggingface.co/
2. Создайте токен: https://huggingface.co/settings/tokens
3. Скопируйте токен

### Шаг 3: Установка переменной окружения (опционально)
```powershell
# Для текущей сессии
$env:HF_TOKEN="ваш_токен_здесь"

# Или постоянная установка
[System.Environment]::SetEnvironmentVariable("HF_TOKEN", "ваш_токен_здесь", "User")
```

**Примечание:** WhisperX автоматически скачает модели при первом использовании.

---

## 3. Проверка установки

После установки перезапустите backend и проверьте логи:
- Должно быть: "✓ Используется оптимизированный сервис распознавания"
- Должно быть: "Используется: Faster-Whisper"
- Должно быть: "Speaker Diarization: Доступен" (если установлен WhisperX)

---

## 4. Использование GPU

### Проверка доступности GPU:
```powershell
.\venv\Scripts\python.exe -c "import torch; print('CUDA доступен:', torch.cuda.is_available())"
```

### Включение GPU:
```powershell
# Для текущей сессии
$env:USE_GPU="true"
.\run_server.ps1

# Или постоянная установка
[System.Environment]::SetEnvironmentVariable("USE_GPU", "true", "User")
```

---

## Производительность

### Без оптимизаций (стандартный Whisper):
- CPU: ~1x скорость
- Память: ~2-4 GB

### С Faster-Whisper:
- CPU: ~4-5x скорость
- GPU: ~10-30x скорость
- Память: ~1-2 GB

### С WhisperX (diarization):
- Дополнительное время: +20-30%
- Требует больше памяти: +1-2 GB

---

## Рекомендации

1. **Для максимальной скорости:**
   - Установите faster-whisper
   - Используйте GPU (если есть)
   - Выберите модель "tiny" или "base"
   - Включите "Режим скорости" в интерфейсе

2. **Для разделения по ролям:**
   - Установите whisperx
   - Укажите количество спикеров (если знаете)
   - Используйте модель "base" или "small" для лучшего качества

3. **Баланс скорости и качества:**
   - Faster-whisper + модель "base"
   - Beam size: 3-5
   - Без diarization (если не нужно)



