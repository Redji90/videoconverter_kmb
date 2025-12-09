import ffmpeg
import os
import tempfile
from pathlib import Path

class VideoProcessor:
    """Класс для обработки видео файлов"""
    
    def extract_audio(self, video_path: str, output_format: str = "wav") -> str:
        """
        Извлекает аудио из видео файла
        
        Args:
            video_path: путь к видео файлу
            output_format: формат выходного аудио (wav, mp3)
        
        Returns:
            путь к извлеченному аудио файлу
        """
        # Создание временного файла для аудио
        audio_path = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=f".{output_format}"
        ).name
        
        try:
            # Извлечение аудио с помощью ffmpeg
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(
                stream,
                audio_path,
                acodec='pcm_s16le' if output_format == 'wav' else 'libmp3lame',
                ac=1,  # моно
                ar='16000'  # частота дискретизации 16kHz (оптимально для Whisper)
            )
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            return audio_path
        
        except ffmpeg.Error as e:
            # Очистка в случае ошибки
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            raise Exception(f"Ошибка при извлечении аудио: {e}")
    
    def get_video_info(self, video_path: str) -> dict:
        """
        Получает информацию о видео файле
        
        Returns:
            словарь с информацией о видео
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_info = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'),
                None
            )
            audio_info = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )
            
            return {
                "duration": float(probe['format'].get('duration', 0)),
                "size": int(probe['format'].get('size', 0)),
                "video_codec": video_info.get('codec_name') if video_info else None,
                "audio_codec": audio_info.get('codec_name') if audio_info else None,
                "width": int(video_info.get('width', 0)) if video_info else None,
                "height": int(video_info.get('height', 0)) if video_info else None,
            }
        except Exception as e:
            raise Exception(f"Ошибка при получении информации о видео: {e}")


