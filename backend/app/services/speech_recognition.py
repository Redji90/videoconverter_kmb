import whisper
import os
from typing import Optional, Dict, List
from pathlib import Path

class SpeechRecognitionService:
    """Сервис для распознавания речи с помощью Whisper"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Инициализация сервиса
        
        Args:
            cache_dir: путь для сохранения моделей Whisper (по умолчанию используется системный кэш)
                      Пример: "E:/whisper-models" или "E:\\whisper-models"
        """
        self.models = {}
        self.default_model = "base"
        
        # Установка пути к кэшу моделей
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            # Создаем директорию, если её нет
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            # Устанавливаем переменную окружения для Whisper
            # ВАЖНО: Whisper ищет модели в WHISPER_CACHE_DIR
            os.environ["WHISPER_CACHE_DIR"] = str(self.cache_dir)
            print(f"Модели Whisper будут сохраняться в: {self.cache_dir}")
            # Проверка наличия модели medium.pt
            model_file = self.cache_dir / "medium.pt"
            if model_file.exists():
                size_mb = model_file.stat().st_size / (1024 * 1024)
                print(f"✓ Найдена модель medium.pt ({size_mb:.0f} MB)")
        else:
            # Используем системный кэш по умолчанию
            self.cache_dir = None
    
    def load_model(self, model_name: str = "base"):
        """
        Загружает модель Whisper
        
        Args:
            model_name: название модели (tiny, base, small, medium, large)
        """
        if model_name not in self.models:
            print(f"Загрузка модели Whisper: {model_name}")
            self.models[model_name] = whisper.load_model(model_name)
            print(f"Модель {model_name} загружена")
        return self.models[model_name]
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model: str = "base"
    ) -> Dict:
        """
        Распознает речь в аудио файле
        
        Args:
            audio_path: путь к аудио файлу
            language: код языка (ISO 639-1, например 'ru', 'en')
            model: модель Whisper для использования
        
        Returns:
            словарь с результатами распознавания
        """
        # Загрузка модели
        whisper_model = self.load_model(model)
        
        # Распознавание
        if language:
            result = whisper_model.transcribe(
                audio_path,
                language=language,
                task="transcribe"
            )
        else:
            # Автоопределение языка
            result = whisper_model.transcribe(
                audio_path,
                task="transcribe"
            )
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": [
                {
                    "id": seg.get("id", i),
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": seg.get("text", "").strip()
                }
                for i, seg in enumerate(result.get("segments", []))
            ]
        }
    
    def generate_subtitles(self, transcription_result: Dict, format: str = "srt") -> str:
        """
        Генерирует субтитры из результата распознавания
        
        Args:
            transcription_result: результат transcribe()
            format: формат субтитров ('srt' или 'vtt')
        
        Returns:
            строка с субтитрами
        """
        segments = transcription_result.get("segments", [])
        
        if format.lower() == "srt":
            return self._generate_srt(segments)
        elif format.lower() == "vtt":
            return self._generate_vtt(segments)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
    
    def _generate_srt(self, segments: List[Dict]) -> str:
        """Генерирует SRT формат"""
        srt_lines = []
        for seg in segments:
            idx = seg.get("id", 0) + 1
            start = self._format_timestamp(seg.get("start", 0))
            end = self._format_timestamp(seg.get("end", 0))
            text = seg.get("text", "")
            
            srt_lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
        
        return "\n".join(srt_lines)
    
    def _generate_vtt(self, segments: List[Dict]) -> str:
        """Генерирует VTT формат"""
        vtt_lines = ["WEBVTT\n"]
        for seg in segments:
            start = self._format_timestamp_vtt(seg.get("start", 0))
            end = self._format_timestamp_vtt(seg.get("end", 0))
            text = seg.get("text", "")
            
            vtt_lines.append(f"{start} --> {end}\n{text}\n")
        
        return "\n".join(vtt_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Форматирует время для SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Форматирует время для VTT (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

