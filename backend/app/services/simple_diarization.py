"""
Простая реализация diarization на основе пауз между сегментами
Не требует дополнительных моделей - работает сразу
"""
from typing import Dict, List


def simple_diarization(segments: List[Dict], pause_threshold: float = 0.3) -> List[Dict]:
    """
    Простое разделение по ролям на основе пауз между сегментами и анализа паттернов диалога
    
    Идея: если между двумя сегментами есть пауза или паттерн диалога (вопрос-ответ),
    то это, вероятно, говорит другой человек.
    
    Args:
        segments: список сегментов из Whisper
                 Каждый сегмент должен иметь 'start' и 'end'
        pause_threshold: минимальная пауза (секунды) для определения нового спикера
                        По умолчанию 0.3 секунды (очень агрессивный порог)
    
    Returns:
        список сегментов с добавленным полем 'speaker'
        Пример: [{'start': 0.0, 'end': 2.5, 'text': '...', 'speaker': 'SPEAKER_00'}, ...]
    """
    if not segments:
        return []
    
    result = []
    current_speaker = "SPEAKER_00"
    speaker_id = 0
    
    # Слова-маркеры вопросов (русский язык)
    question_words = ['как', 'что', 'где', 'когда', 'кто', 'почему', 'зачем', 'какой', 'какая', 'какое', 
                      'расскажи', 'скажи', 'поделись', 'поделишься', 'можешь', 'может', 'есть']
    
    # Анализируем сегменты для определения паттернов диалога
    for i, segment in enumerate(segments):
        # Если это первый сегмент - всегда SPEAKER_00
        if i == 0:
            new_segment = dict(segment)
            new_segment["speaker"] = current_speaker
            result.append(new_segment)
            continue
        
        # Вычисляем паузу между предыдущим и текущим сегментами
        prev_end = segments[i-1].get("end", 0)
        curr_start = segment.get("start", 0)
        pause = curr_start - prev_end
        
        # Дополнительная проверка: длительность текущего и предыдущего сегментов
        seg_duration = segment.get("end", curr_start) - curr_start
        prev_duration = segments[i-1].get("end", 0) - segments[i-1].get("start", 0)
        
        # Анализ текста для определения вопросов и ответов
        text = segment.get("text", "").strip().lower()
        prev_text = segments[i-1].get("text", "").strip()
        prev_text_lower = prev_text.lower()
        
        # Определяем, является ли предыдущий сегмент вопросом
        is_question = (
            prev_text.endswith(('?', '?')) or
            any(prev_text_lower.startswith(qw + ' ') or prev_text_lower.startswith(qw + ',') 
                for qw in question_words) or
            '?' in prev_text
        )
        
        # Определяем, является ли текущий сегмент ответом (начинается с "да", "нет", "это" и т.д.)
        is_answer = (
            text.startswith(('да', 'нет', 'это', 'я', 'мы', 'он', 'она', 'они', 'моя', 'мой', 'моё'))
        )
        
        # Эвристики для определения смены спикера (более агрессивные):
        # 1. Пауза >= threshold (даже короткая)
        # 2. Пауза > 0.2 сек + предыдущий сегмент - вопрос → новый спикер отвечает
        # 3. Пауза > 0.2 сек + текущий сегмент начинается как ответ → новый спикер
        # 4. Пауза > 0.25 сек → новый спикер
        # 5. Пауза > 0.15 сек + предыдущий сегмент длинный (> 2 сек) → новый спикер
        # 6. Чередование длинных и коротких сегментов с паузами
        
        should_change_speaker = False
        
        if pause >= pause_threshold:
            # Пауза больше порога - новый спикер
            should_change_speaker = True
        elif pause > 0.25:
            # Пауза больше 0.25 сек - новый спикер
            should_change_speaker = True
        elif pause > 0.2 and is_question:
            # Пауза после вопроса - новый спикер отвечает
            should_change_speaker = True
        elif pause > 0.2 and is_answer:
            # Пауза перед ответом - новый спикер
            should_change_speaker = True
        elif pause > 0.15 and prev_duration > 2.0:
            # Пауза после длинной реплики - новый спикер
            should_change_speaker = True
        elif pause > 0.15 and seg_duration < 1.0 and prev_duration > 1.5:
            # Короткий ответ после длинной реплики - новый спикер
            should_change_speaker = True
        
        # Дополнительная эвристика: если уже есть 2+ спикера, чередуем их
        # Это помогает в диалогах с четким чередованием
        if not should_change_speaker and speaker_id > 0 and pause > 0.1:
            # Если пауза есть и уже есть несколько спикеров, чередуем
            # Но только если предыдущий сегмент был достаточно длинным
            if prev_duration > 1.0:
                should_change_speaker = True
        
        # ОЧЕНЬ АГРЕССИВНАЯ эвристика: если пауза есть (даже минимальная) и это не первый спикер,
        # и предыдущий сегмент был достаточно длинным, чередуем спикеров
        # Это помогает в диалогах без явных пауз
        if not should_change_speaker and pause > 0.05 and prev_duration > 0.8:
            # Если есть хоть какая-то пауза и предыдущий сегмент длинный - чередуем
            # Но только если мы уже определили хотя бы одного спикера
            if speaker_id >= 0:  # Всегда чередуем после первого спикера
                should_change_speaker = True
        
        if should_change_speaker:
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


