# Альтернативы Diarization (простое решение)

## 🎯 Проблема

Модель `pyannote/segmentation-3.0` не скачивается из-за проблем с авторизацией или сетью.

## ✅ Решение 1: Использовать старую версию pyannote (РЕКОМЕНДУЕТСЯ)

### pyannote/speaker-diarization-2.1

**Преимущества:**
- ✅ Не требует `segmentation-3.0`
- ✅ Может не требовать авторизацию
- ✅ Хорошая точность
- ✅ Работает с WhisperX

**Установка:**
```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1

# Проверить, какая версия pyannote установлена
pip show pyannote.audio

# Если нужно, установить/обновить
pip install pyannote.audio==3.1.1
```

**Использование:**

1. Проверьте доступность модели:
```powershell
python test_diarization_alternatives.py
```

2. Если модель доступна, обновите код:

В `backend/app/services/speech_recognition_optimized.py`, измените строку 246:

```python
# Было:
diarize_model = whisperx.DiarizationPipeline(
    use_auth_token=hf_token,
    device=device
)

# Стало (для версии 2.1):
diarize_model = whisperx.DiarizationPipeline(
    use_auth_token=hf_token,
    device=device,
    model_name="pyannote/speaker-diarization-2.1"  # Добавьте эту строку
)
```

**Если WhisperX не поддерживает указание модели:**

Используйте pyannote напрямую:

```python
from pyannote.audio import Pipeline

# В методе _transcribe_with_diarization:
diarize_model = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-2.1",
    use_auth_token=hf_token
)
diarize_model.to(device)

# Использование:
diarization = diarize_model({"audio": audio_path})
```

---

## ✅ Решение 2: Простая эвристика на основе пауз (РАБОТАЕТ СРАЗУ)

**Идея:** Определяем нового спикера по длинным паузам между сегментами.

**Преимущества:**
- ✅ Работает сразу, без дополнительных моделей
- ✅ Не требует интернет
- ✅ Быстро
- ✅ Подходит для простых случаев (интервью, диалоги)

**Недостатки:**
- ⚠️ Менее точное, чем pyannote
- ⚠️ Не работает при перекрывающейся речи
- ⚠️ Может ошибаться при быстрой смене спикеров

**Реализация:**

Создайте файл `backend/app/services/simple_diarization.py`:

```python
"""
Простая реализация diarization на основе пауз между сегментами
"""
from typing import Dict, List

def simple_diarization(segments: List[Dict], pause_threshold: float = 1.0) -> List[Dict]:
    """
    Простое разделение по ролям на основе пауз
    
    Args:
        segments: список сегментов из Whisper
        pause_threshold: минимальная пауза (сек) для нового спикера
    
    Returns:
        список сегментов с добавленным полем 'speaker'
    """
    if not segments:
        return []
    
    result = []
    current_speaker = "SPEAKER_00"
    speaker_id = 0
    
    for i, segment in enumerate(segments):
        # Если это первый сегмент - всегда SPEAKER_00
        if i == 0:
            segment["speaker"] = current_speaker
            result.append(segment)
            continue
        
        # Вычисляем паузу между сегментами
        prev_end = segments[i-1].get("end", 0)
        curr_start = segment.get("start", 0)
        pause = curr_start - prev_end
        
        # Если пауза достаточно длинная - новый спикер
        if pause >= pause_threshold:
            speaker_id += 1
            current_speaker = f"SPEAKER_{speaker_id:02d}"
        
        segment["speaker"] = current_speaker
        result.append(segment)
    
    return result
```

**Использование в `speech_recognition_optimized.py`:**

Добавьте импорт:
```python
from .simple_diarization import simple_diarization
```

Измените метод `transcribe`:

```python
# Вместо enable_diarization и WHISPERX_AVAILABLE:
if enable_diarization:
    # Простая diarization на основе пауз
    result = self._transcribe_standard(audio_path, language, model, beam_size, best_of)
    result["segments"] = simple_diarization(result["segments"], pause_threshold=1.0)
    
    # Группировка по спикерам
    speakers_text = {}
    for seg in result["segments"]:
        speaker = seg.get("speaker", "SPEAKER_00")
        if speaker not in speakers_text:
            speakers_text[speaker] = []
        speakers_text[speaker].append(seg["text"])
    
    result["speakers"] = {
        speaker: " ".join(texts)
        for speaker, texts in speakers_text.items()
    }
    result["num_speakers"] = len(speakers_text)
    
    return result
```

---

## ✅ Решение 3: SpeechBrain (альтернативная библиотека)

**Установка:**
```powershell
pip install speechbrain
```

**Использование:**
```python
from speechbrain.inference.speaker import SpeakerRecognition

# Создание модели
model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="pretrained_models/spkrec-ecapa-voxceleb"
)

# Извлечение embedding'ов для кластеризации
# (требует дополнительной обработки для diarization)
```

**Примечание:** SpeechBrain больше подходит для speaker verification, чем для diarization. Потребуется дополнительная кластеризация.

---

## 📊 Сравнение решений

| Решение | Точность | Скорость | Простота | Требует модели |
|---------|----------|----------|----------|----------------|
| **pyannote-2.1** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ✅ Да (~1.2 GB) |
| **Простая эвристика** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ Нет |
| **SpeechBrain** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ✅ Да (~500 MB) |

---

## 🚀 Быстрое внедрение (Рекомендуется)

### Вариант A: Простая эвристика (работает сразу)

1. Создайте файл `backend/app/services/simple_diarization.py` с кодом выше
2. Обновите `speech_recognition_optimized.py` как описано
3. Готово! Diarization работает без дополнительных моделей

### Вариант B: pyannote-2.1 (лучшая точность)

1. Запустите: `python test_diarization_alternatives.py`
2. Если модель доступна, обновите код как описано выше
3. Перезапустите сервер

---

## 💡 Рекомендация

**Начните с Варианта A (простая эвристика)** - работает сразу и дает приемлемый результат для большинства случаев (диалоги, интервью).

Если нужна высокая точность - переходите к **Варианту B (pyannote-2.1)**.


