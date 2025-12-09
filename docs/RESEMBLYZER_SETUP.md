# Установка и использование Resemblyzer

Resemblyzer - легковесная альтернатива для speaker diarization (~50 MB), которая не требует авторизацию HuggingFace.

## 📥 Установка

### ⚠️ Важно для Windows

На Windows может потребоваться **Microsoft Visual C++ Build Tools** для компиляции `webrtcvad`.

**Если возникла ошибка компиляции, см. подробную инструкцию:** `backend/RESEMBLYZER_WINDOWS_FIX.md`

### Шаг 1: Установите Resemblyzer

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install resemblyzer librosa soundfile
```

**Если ошибка с webrtcvad:**

1. **Быстрое решение:** Установите Build Tools:
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Выберите "Desktop development with C++"
   - После установки перезапустите PowerShell

2. **Альтернатива:** Попробуйте предкомпилированную версию:
   ```powershell
   pip install pipwin
   pipwin install webrtcvad
   pip install resemblyzer librosa soundfile
   ```

Или если виртуальное окружение не активировано:

```powershell
cd backend
.\venv\Scripts\python.exe -m pip install resemblyzer librosa soundfile
```

## 🚀 Использование

### Базовый пример

```python
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np

# Загрузите аудио
wav_fpath = Path("audio.wav")
wav = preprocess_wav(wav_fpath)

# Создайте энкодер
encoder = VoiceEncoder()

# Получите embedding (векторное представление голоса)
embed = encoder.embed_utterance(wav)
print(f"Embedding shape: {embed.shape}")
```

### Speaker Diarization с Resemblyzer

Resemblyzer не имеет встроенной функции diarization, но можно использовать для кластеризации спикеров:

```python
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path
import numpy as np
from sklearn.cluster import AgglomerativeClustering

def diarize_with_resemblyzer(audio_path, num_speakers=None):
    """
    Простая diarization с использованием Resemblyzer
    """
    # Загрузите и предобработайте аудио
    wav = preprocess_wav(audio_path)
    
    # Создайте энкодер
    encoder = VoiceEncoder()
    
    # Разделите аудио на сегменты (например, по 1.5 секунды)
    segment_length = 1.5  # секунды
    sample_rate = 16000
    segment_samples = int(segment_length * sample_rate)
    
    segments = []
    embeddings = []
    
    for i in range(0, len(wav), segment_samples):
        segment = wav[i:i + segment_samples]
        if len(segment) < segment_samples:
            # Дополните последний сегмент нулями
            segment = np.pad(segment, (0, segment_samples - len(segment)))
        
        # Получите embedding для сегмента
        embed = encoder.embed_utterance(segment)
        embeddings.append(embed)
        segments.append(i / sample_rate)  # время начала сегмента
    
    # Кластеризация спикеров
    embeddings = np.array(embeddings)
    
    if num_speakers is None:
        # Автоматическое определение количества спикеров
        # Используйте метод локтя или другой метод
        num_speakers = 2  # по умолчанию
    
    clustering = AgglomerativeClustering(n_clusters=num_speakers)
    labels = clustering.fit_predict(embeddings)
    
    # Формируем результат
    result = {
        "segments": [],
        "speakers": {}
    }
    
    for i, (time, label) in enumerate(zip(segments, labels)):
        speaker = f"SPEAKER_{label:02d}"
        result["segments"].append({
            "start": time,
            "end": time + segment_length,
            "speaker": speaker
        })
        
        if speaker not in result["speakers"]:
            result["speakers"][speaker] = []
    
    return result
```

## 🔧 Интеграция в проект

Чтобы использовать Resemblyzer вместо pyannote в вашем проекте, нужно модифицировать `speech_recognition_optimized.py`:

### Вариант 1: Добавить Resemblyzer как альтернативу

```python
# В начале файла
try:
    from resemblyzer import VoiceEncoder, preprocess_wav
    RESEMBLYZER_AVAILABLE = True
except ImportError:
    RESEMBLYZER_AVAILABLE = False

# В методе _transcribe_with_diarization
if RESEMBLYZER_AVAILABLE and not WHISPERX_AVAILABLE:
    # Используйте Resemblyzer
    return self._transcribe_with_resemblyzer(audio_path, language, model, num_speakers)
```

### Вариант 2: Создать отдельный сервис

Создайте файл `backend/app/services/speech_recognition_resemblyzer.py`:

```python
from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from typing import Dict, Optional

class ResemblyzerDiarizationService:
    def __init__(self):
        self.encoder = VoiceEncoder()
    
    def diarize(self, audio_path: str, num_speakers: Optional[int] = None) -> Dict:
        # Реализация diarization с Resemblyzer
        # (см. пример выше)
        pass
```

## ⚖️ Сравнение с Pyannote

| Характеристика | Resemblyzer | Pyannote |
|----------------|-------------|----------|
| Размер | ~50 MB | ~1.5 GB |
| Требует авторизацию | ❌ Нет | ✅ Да |
| Точность | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Скорость | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Простота | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Поддержка | ⚠️ Ограниченная | ✅ Активная |

## 💡 Рекомендации

**Используйте Resemblyzer, если:**
- ✅ Нужна быстрая и легкая модель
- ✅ Не хотите возиться с авторизацией HuggingFace
- ✅ Точность не критична
- ✅ Ограниченные ресурсы

**Используйте Pyannote, если:**
- ✅ Нужна максимальная точность
- ✅ Готовы настроить авторизацию
- ✅ Есть достаточно места на диске

## 🔍 Решение проблемы с segmentation-3.0

Если `segmentation-3.0` не скачивается, это потому что она требует:

1. **Принятия условий использования:**
   - Перейдите: https://huggingface.co/pyannote/segmentation-3.0
   - Войдите в аккаунт
   - Нажмите "Accept"

2. **Токена HuggingFace:**
   - Получите токен: https://huggingface.co/settings/tokens
   - Установите: `$env:HF_TOKEN="ваш_токен"`

3. **Повторная попытка:**
   ```powershell
   $env:HF_TOKEN="ваш_токен"
   python download_diarization_model.py
   ```

**Альтернатива:** Используйте Resemblyzer - он не требует segmentation-3.0!

## 📝 Пример полного использования

```python
# test_resemblyzer.py
from resemblyzer import VoiceEncoder, preprocess_wav
from pathlib import Path

# Загрузите аудио
audio_path = Path("test_audio.wav")
wav = preprocess_wav(audio_path)

# Создайте энкодер
encoder = VoiceEncoder()

# Получите embedding
embed = encoder.embed_utterance(wav)
print(f"Embedding получен! Размер: {embed.shape}")

# Для diarization нужно разделить на сегменты и кластеризовать
# (см. пример выше)
```

## 🔗 Полезные ссылки

- GitHub: https://github.com/resemble-ai/Resemblyzer
- Документация: https://github.com/resemble-ai/Resemblyzer#usage
- Примеры: https://github.com/resemble-ai/Resemblyzer/tree/master/demo

