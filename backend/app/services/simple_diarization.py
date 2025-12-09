"""
Простая реализация diarization на основе пауз между сегментами
Не требует дополнительных моделей - работает сразу
"""
from typing import Dict, List


def simple_diarization(segments: List[Dict], pause_threshold: float = 1.0) -> List[Dict]:
    """
    Простое разделение по ролям на основе пауз между сегментами
    
    Идея: если между двумя сегментами есть длинная пауза (> threshold),
    то это, вероятно, говорит другой человек.
    
    Args:
        segments: список сегментов из Whisper
                 Каждый сегмент должен иметь 'start' и 'end'
        pause_threshold: минимальная пауза (секунды) для определения нового спикера
                        По умолчанию 1.0 секунда
    
    Returns:
        список сегментов с добавленным полем 'speaker'
        Пример: [{'start': 0.0, 'end': 2.5, 'text': '...', 'speaker': 'SPEAKER_00'}, ...]
    """
    if not segments:
        return []
    
    result = []
    current_speaker = "SPEAKER_00"
    speaker_id = 0
    
    for i, segment in enumerate(segments):
        # Если это первый сегмент - всегда SPEAKER_00
        if i == 0:
            # Создаем копию сегмента с добавленным полем speaker
            new_segment = dict(segment)
            new_segment["speaker"] = current_speaker
            result.append(new_segment)
            continue
        
        # Вычисляем паузу между предыдущим и текущим сегментами
        prev_end = segments[i-1].get("end", 0)
        curr_start = segment.get("start", 0)
        pause = curr_start - prev_end
        
        # Если пауза достаточно длинная - это новый спикер
        if pause >= pause_threshold:
            speaker_id += 1
            current_speaker = f"SPEAKER_{speaker_id:02d}"
        
        # Добавляем поле speaker к сегменту
        new_segment = dict(segment)
        new_segment["speaker"] = current_speaker
        result.append(new_segment)
    
    return result


def group_by_speakers(segments: List[Dict]) -> Dict[str, str]:
    """
    Группирует текст по спикерам
    
    Args:
        segments: список сегментов с полем 'speaker'
    
    Returns:
        словарь {speaker: текст}
    """
    speakers_text = {}
    
    for seg in segments:
        speaker = seg.get("speaker", "SPEAKER_00")
        text = seg.get("text", "").strip()
        
        if not text:
            continue
        
        if speaker not in speakers_text:
            speakers_text[speaker] = []
        
        speakers_text[speaker].append(text)
    
    # Объединяем текст каждого спикера
    return {
        speaker: " ".join(texts)
        for speaker, texts in speakers_text.items()
    }


