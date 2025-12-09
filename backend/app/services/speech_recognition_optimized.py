"""
Оптимизированный сервис распознавания речи с поддержкой:
- Faster-Whisper для ускорения
- Speaker Diarization (разделение по ролям)
"""
import os
from typing import Optional, Dict, List
from pathlib import Path

# Отключение XET для избежания проблем с зависанием загрузок на Windows
# XET часто вызывает таймауты при скачивании больших файлов
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# ВАЖНО: Устанавливаем WHISPER_CACHE_DIR ДО импорта whisper
# Whisper использует этот путь при импорте модуля
# Если не установлен - проверяем переменную окружения или config
if "WHISPER_CACHE_DIR" not in os.environ:
    # Пробуем получить из config
    try:
        import sys
        # Пробуем импортировать config
        config_path = Path(__file__).parent.parent.parent / "config.py"
        if config_path.exists():
            # Добавляем путь к sys.path для импорта
            sys.path.insert(0, str(config_path.parent))
            try:
                from config import WHISPER_CACHE_DIR as CONFIG_CACHE_DIR
                if CONFIG_CACHE_DIR:
                    os.environ["WHISPER_CACHE_DIR"] = CONFIG_CACHE_DIR
            except ImportError:
                # Если импорт не удался, пробуем прочитать файл напрямую
                import re
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Ищем WHISPER_CACHE_DIR = "E:\\whisper-models"
                    match = re.search(r'WHISPER_CACHE_DIR.*?=.*?["\']([^"\']+)["\']', content)
                    if match:
                        os.environ["WHISPER_CACHE_DIR"] = match.group(1)
    except Exception:
        # Если ничего не получилось, пробуем стандартный путь
        default_path = "E:\\whisper-models"
        if Path(default_path).exists():
            os.environ["WHISPER_CACHE_DIR"] = default_path

# Попытка импорта faster-whisper (оптимизированная версия)
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    # ВАЖНО: Импорт whisper происходит здесь, после установки WHISPER_CACHE_DIR
    import whisper

# ВАЖНО: Применяем патч torch.load ДО импорта WhisperX/pyannote
# чтобы патч применялся к внутренним вызовам torch.load в этих библиотеках
# Используем глобальную переменную модуля для сохранения оригинальной функции
# Это предотвращает рекурсию при повторных вызовах
_torch_load_original_global = None

try:
    import torch
    
    # Сохраняем оригинальную функцию ДО патча (в глобальной переменной модуля)
    # Проверяем, что она еще не была сохранена (защита от повторного импорта)
    if _torch_load_original_global is None:
        _torch_load_original_global = torch.load
    
    # Патч для torch.load чтобы использовать weights_only=False для pyannote
    # PyTorch 2.6+ требует явного указания weights_only=False для моделей pyannote
    def _torch_load_patched_final(*args, **kwargs):
        # Устанавливаем weights_only=False для pyannote (доверенный источник HuggingFace)
        kwargs['weights_only'] = False
        # КРИТИЧНО: Используем сохраненную оригинальную функцию из глобальной переменной
        # НЕ используем torch.load, чтобы избежать рекурсии!
        return _torch_load_original_global(*args, **kwargs)
    
    # Применяем патч для PyTorch 2.6+ (версия 2.8.0 точно требует этого)
    try:
        torch_version = torch.__version__
        major, minor = map(int, torch_version.split('.')[:2])
        if major > 2 or (major == 2 and minor >= 6):
            torch.load = _torch_load_patched_final
    except:
        # Если не удалось определить версию, применяем патч для безопасности
        # (лучше перестраховаться)
        torch.load = _torch_load_patched_final
except Exception:
    # Если патч не применился, продолжаем без него (может вызвать ошибку при загрузке моделей)
    pass

# Попытка импорта WhisperX для diarization
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False

# Простая diarization на основе пауз (fallback, если WhisperX недоступен)
try:
    from .simple_diarization import simple_diarization, group_by_speakers
    SIMPLE_DIARIZATION_AVAILABLE = True
except ImportError:
    SIMPLE_DIARIZATION_AVAILABLE = False


class OptimizedSpeechRecognitionService:
    """Оптимизированный сервис для распознавания речи"""
    
    def __init__(self, cache_dir: Optional[str] = None, use_gpu: bool = False, device: str = "auto"):
        """
        Инициализация сервиса
        
        Args:
            cache_dir: путь для сохранения моделей
            use_gpu: использовать GPU (если доступен)
            device: устройство для обработки ("cuda", "cpu", "auto")
        """
        self.models = {}
        self.default_model = "base"
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.use_gpu = use_gpu
        self.device = device
        
        # Определение устройства
        if device == "auto":
            if use_gpu and FASTER_WHISPER_AVAILABLE:
                # Проверка доступности CUDA
                try:
                    import torch
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                except:
                    self.device = "cpu"
            else:
                self.device = "cpu"
        
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ["WHISPER_CACHE_DIR"] = str(self.cache_dir)
            print(f"Модели будут сохраняться в: {self.cache_dir}")
            # Проверка наличия моделей в кэше (для стандартного Whisper)
            if not FASTER_WHISPER_AVAILABLE:
                for model_name in ["tiny", "base", "small", "medium", "large"]:
                    model_file = self.cache_dir / f"{model_name}.pt"
                    if model_file.exists():
                        size_gb = model_file.stat().st_size / (1024 * 1024 * 1024)
                        print(f"  ✓ Найдена модель {model_name}.pt ({size_gb:.2f} GB)")
        
        print(f"Используется: {'Faster-Whisper' if FASTER_WHISPER_AVAILABLE else 'Standard Whisper'}")
        print(f"Устройство: {self.device}")
        if WHISPERX_AVAILABLE:
            print(f"Speaker Diarization: Доступен (WhisperX)")
        elif SIMPLE_DIARIZATION_AVAILABLE:
            print(f"Speaker Diarization: Доступен (простая версия на основе пауз)")
        else:
            print(f"Speaker Diarization: Недоступен")
    
    def load_model(self, model_name: str = "base"):
        """Загружает модель"""
        if model_name not in self.models:
            print(f"[LOAD_MODEL] Начало загрузки модели: {model_name}")
            print(f"[LOAD_MODEL] FASTER_WHISPER_AVAILABLE: {FASTER_WHISPER_AVAILABLE}")
            print(f"[LOAD_MODEL] Устройство: {self.device}")
            
            if FASTER_WHISPER_AVAILABLE:
                # Используем faster-whisper (быстрее)
                download_path = str(self.cache_dir) if self.cache_dir else None
                
                # Отключаем XET для избежания проблем с зависанием
                # Это нужно сделать перед созданием WhisperModel
                os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
                
                # Проверяем, существует ли модель в формате Faster-Whisper
                if download_path:
                    model_path = Path(download_path) / model_name
                    if model_path.exists() and any(model_path.iterdir()):
                        print(f"  Найдена модель Faster-Whisper в: {model_path}")
                    else:
                        # Проверяем, есть ли .pt файл (стандартный Whisper)
                        pt_file = Path(download_path) / f"{model_name}.pt"
                        if pt_file.exists():
                            print(f"  ⚠ ВНИМАНИЕ: Найден файл {model_name}.pt (формат стандартного Whisper)")
                            print(f"  ⚠ Faster-Whisper использует другой формат (CTranslate2)")
                            print(f"  ⚠ Модель будет скачана в формате Faster-Whisper в: {model_path}")
                            print(f"  ℹ Это нормально - после скачивания модель сохранится и больше не будет скачиваться")
                        else:
                            print(f"  Модель не найдена, будет скачана в: {download_path}")
                    print(f"  Используется Faster-Whisper (формат CTranslate2)")
                
                print(f"[LOAD_MODEL] Создание WhisperModel для {model_name}...")
                print(f"[LOAD_MODEL] Параметры: device={self.device}, compute_type={'float16' if self.device == 'cuda' else 'int8'}, download_root={download_path}")
                try:
                    self.models[model_name] = WhisperModel(
                        model_name,
                        device=self.device,
                        compute_type="float16" if self.device == "cuda" else "int8",
                        download_root=download_path
                    )
                    print(f"[LOAD_MODEL] ✓ WhisperModel создан успешно")
                except Exception as e:
                    print(f"[LOAD_MODEL] ❌ Ошибка при создании WhisperModel: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            else:
                # Fallback на стандартный Whisper
                print(f"  Используется стандартный Whisper (формат .pt)")
                # Проверяем, установлен ли WHISPER_CACHE_DIR
                whisper_cache = os.environ.get("WHISPER_CACHE_DIR")
                if whisper_cache:
                    print(f"  Используется кэш: {whisper_cache}")
                    model_file = Path(whisper_cache) / f"{model_name}.pt"
                    if model_file.exists():
                        size_gb = model_file.stat().st_size / (1024 * 1024 * 1024)
                        print(f"  ✓ Модель найдена в кэше: {model_file} ({size_gb:.2f} GB)")
                    else:
                        print(f"  ⚠ Модель не найдена в {whisper_cache}, будет скачана")
                else:
                    print(f"  ⚠ WHISPER_CACHE_DIR не установлен, используется системный кэш")
                print(f"[LOAD_MODEL] Загрузка стандартной модели Whisper: {model_name}")
                try:
                    self.models[model_name] = whisper.load_model(model_name)
                    print(f"[LOAD_MODEL] ✓ Стандартная модель Whisper загружена")
                except Exception as e:
                    print(f"[LOAD_MODEL] ❌ Ошибка при загрузке стандартной модели: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
            
            print(f"[LOAD_MODEL] ✓ Модель {model_name} полностью загружена и готова к использованию")
        return self.models[model_name]
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model: str = "base",
        beam_size: int = 5,
        best_of: int = 5,
        enable_diarization: bool = False,
        num_speakers: Optional[int] = None,
        speaker_names: Optional[List[str]] = None,
        translate_to_english: bool = False
    ) -> Dict:
        """
        Распознает речь с опциональным разделением по ролям и переводом на английский
        
        Args:
            audio_path: путь к аудио
            language: код языка
            model: модель Whisper
            beam_size: размер луча (меньше = быстрее, но менее точно)
            best_of: количество попыток (меньше = быстрее)
            enable_diarization: включить разделение по ролям
            num_speakers: количество спикеров (None = автоопределение)
            translate_to_english: перевести результат на английский язык
        
        Returns:
            словарь с результатами
        """
        # Diarization: сначала пробуем WhisperX, если недоступен - используем простую эвристику
        # Примечание: diarization с переводом не поддерживается (нужно сначала транскрибировать, потом переводить)
        if enable_diarization and not translate_to_english:
            if WHISPERX_AVAILABLE:
                try:
                    return self._transcribe_with_diarization(
                        audio_path, language, model, num_speakers, speaker_names
                    )
                except Exception as e:
                    print(f"⚠️  WhisperX diarization не удалось: {e}")
                    print("   Используем простую diarization на основе пауз")
                    # Fallback на простую diarization (только если не требуется перевод)
                    if SIMPLE_DIARIZATION_AVAILABLE and not translate_to_english:
                        try:
                            return self._transcribe_with_simple_diarization(
                                audio_path, language, model, beam_size, best_of, speaker_names
                            )
                        except Exception as e2:
                            print(f"❌ Простая diarization также не удалась: {e2}")
                            print("   Продолжаем без diarization")
                            # Продолжаем с обычной транскрипцией
                    else:
                        print("   Простая diarization недоступна - продолжаем без разделения по ролям")
            elif SIMPLE_DIARIZATION_AVAILABLE and not translate_to_english:
                # Используем простую diarization, если WhisperX не установлен (только если не требуется перевод)
                try:
                    return self._transcribe_with_simple_diarization(
                        audio_path, language, model, beam_size, best_of, speaker_names
                    )
                except Exception as e:
                    print(f"❌ Простая diarization не удалась: {e}")
                    print("   Продолжаем без diarization")
                    # Продолжаем с обычной транскрипцией
        
        # Стандартная транскрипция (быстрее)
        print(f"[TRANSCRIBE] Загрузка модели {model}...")
        whisper_model = self.load_model(model)
        print(f"[TRANSCRIBE] Модель {model} загружена, начинаем транскрипцию...")
        
        # Всегда делаем транскрипцию на исходном языке
        # Если нужен перевод - делаем дополнительный вызов
        if translate_to_english:
            print(f"🌐 Режим перевода включен: будет выполнен перевод в дополнение к транскрипции")
        
        if FASTER_WHISPER_AVAILABLE:
            # Faster-Whisper API - сначала транскрипция на исходном языке
            print(f"[TRANSCRIBE] Выполнение транскрипции на исходном языке (Faster-Whisper)...")
            print(f"[TRANSCRIBE] Параметры: language={language}, beam_size={beam_size}, best_of={best_of}")
            try:
                segments, info = whisper_model.transcribe(
                    audio_path,
                    language=language,
                    beam_size=beam_size,
                    best_of=best_of,
                    vad_filter=True,  # Voice Activity Detection для ускорения
                    vad_parameters=dict(min_silence_duration_ms=500)
                )
                print(f"[TRANSCRIBE] ✓ Транскрипция завершена, обработка сегментов...")
            except Exception as e:
                print(f"[TRANSCRIBE] ❌ Ошибка при транскрипции: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Конвертация в нужный формат
            segments_list = []
            full_text_parts = []
            
            for segment in segments:
                seg_dict = {
                    "id": len(segments_list),
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                }
                segments_list.append(seg_dict)
                full_text_parts.append(segment.text.strip())
            
            # Формируем результат с оригинальным текстом
            result = {
                "text": " ".join(full_text_parts),
                "language": info.language,
                "segments": segments_list,
                "has_translation": False
            }
            
            # Если нужен перевод - делаем дополнительный вызов через стандартный Whisper
            if translate_to_english:
                print(f"[TRANSLATE] Начало перевода на английский...")
                print(f"[TRANSLATE] ⚠️  Faster-Whisper не поддерживает перевод, используем стандартный Whisper")
                import whisper
                try:
                    standard_model = whisper.load_model(model)
                    print(f"[TRANSLATE] Стандартная модель загружена, начинаем перевод...")
                    translate_result = standard_model.transcribe(
                        audio_path,
                        language=language,
                        task="translate",
                        beam_size=beam_size,
                        best_of=best_of
                    )
                    print(f"[TRANSLATE] ✓ Перевод завершен")
                    
                    # Формируем результат перевода
                    translated_segments = [
                        {
                            "id": seg.get("id", i),
                            "start": seg.get("start", 0),
                            "end": seg.get("end", 0),
                            "text": seg.get("text", "").strip()
                        }
                        for i, seg in enumerate(translate_result.get("segments", []))
                    ]
                    
                    result["translated_text"] = translate_result["text"].strip()
                    result["translated_language"] = "en"
                    result["translated_segments"] = translated_segments
                    result["has_translation"] = True
                except Exception as e:
                    print(f"[TRANSLATE] ❌ Ошибка при переводе: {e}")
                    import traceback
                    traceback.print_exc()
                    # Продолжаем без перевода, возвращаем только оригинал
                    print(f"[TRANSLATE] ⚠️  Продолжаем без перевода")
                    result["has_translation"] = False
            
            return result
        else:
            # Стандартный Whisper - сначала транскрипция на исходном языке
            print(f"[TRANSCRIBE] Выполнение транскрипции на исходном языке (стандартный Whisper)...")
            original_result = whisper_model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                beam_size=beam_size,
                best_of=best_of
            )
            
            original_segments = [
                {
                    "id": seg.get("id", i),
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": seg.get("text", "").strip()
                }
                for i, seg in enumerate(original_result.get("segments", []))
            ]
            
            result = {
                "text": original_result["text"].strip(),
                "language": original_result.get("language", "unknown"),
                "segments": original_segments,
                "has_translation": False
            }
            
            # Если нужен перевод - делаем дополнительный вызов
            if translate_to_english:
                print(f"[TRANSLATE] Начало перевода на английский (стандартный Whisper)...")
                try:
                    translate_result = whisper_model.transcribe(
                        audio_path,
                        language=language,
                        task="translate",
                        beam_size=beam_size,
                        best_of=best_of
                    )
                    print(f"[TRANSLATE] ✓ Перевод завершен")
                    
                    translated_segments = [
                        {
                            "id": seg.get("id", i),
                            "start": seg.get("start", 0),
                            "end": seg.get("end", 0),
                            "text": seg.get("text", "").strip()
                        }
                        for i, seg in enumerate(translate_result.get("segments", []))
                    ]
                    
                    result["translated_text"] = translate_result["text"].strip()
                    result["translated_language"] = "en"
                    result["translated_segments"] = translated_segments
                    result["has_translation"] = True
                except Exception as e:
                    print(f"[TRANSLATE] ❌ Ошибка при переводе: {e}")
                    import traceback
                    traceback.print_exc()
                    result["has_translation"] = False
            
            return result
    
    def _transcribe_with_diarization(
        self,
        audio_path: str,
        language: Optional[str],
        model: str,
        num_speakers: Optional[int],
        speaker_names: Optional[List[str]] = None
    ) -> Dict:
        """Транскрипция с разделением по ролям (требует WhisperX)"""
        if not WHISPERX_AVAILABLE:
            raise ImportError("WhisperX не установлен. Установите: pip install whisperx")
        
        # Установка пути для HuggingFace, если указан
        hf_home = os.getenv("HF_HOME")
        if hf_home:
            os.environ["HF_HOME"] = hf_home
            print(f"Используется HF_HOME: {hf_home}")
        
        # Загрузка модели
        device = "cuda" if self.use_gpu and self.device == "cuda" else "cpu"
        
        # WhisperX может использовать стандартный Whisper, поэтому нужно указать путь к кэшу
        if self.cache_dir:
            # WhisperX ищет модели в стандартном месте или через переменную окружения
            os.environ["WHISPER_CACHE_DIR"] = str(self.cache_dir)
            print(f"Используется WHISPER_CACHE_DIR для WhisperX: {self.cache_dir}")
        
        # Используем Faster-Whisper для транскрипции (более надежно)
        # Затем применяем pyannote.audio для diarization
        print(f"Загрузка модели Whisper: {model} (устройство: {device})")
        
        # Загружаем модель через Faster-Whisper напрямую
        if FASTER_WHISPER_AVAILABLE:
            from faster_whisper import WhisperModel
            download_path = str(self.cache_dir) if self.cache_dir else None
            whisper_model = WhisperModel(
                model,
                device=device,
                compute_type="int8" if device == "cpu" else "float16",
                download_root=download_path
            )
            print(f"Модель Whisper {model} загружена через Faster-Whisper")
            
            # Транскрипция
            print("Выполняется транскрипция...")
            segments, info = whisper_model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Конвертация в нужный формат
            segments_list = []
            for segment in segments:
                segments_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
            
            result = {
                "language": info.language,
                "segments": segments_list
            }
        else:
            # Fallback на стандартный Whisper
            import whisper
            whisper_model = whisper.load_model(model)
            result = whisper_model.transcribe(audio_path, language=language)
            result = {
                "language": result.get("language", "unknown"),
                "segments": [
                    {
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "").strip()
                    }
                    for seg in result.get("segments", [])
                ]
            }
        
        print(f"✓ Транскрипция завершена: {len(result['segments'])} сегментов")
        
        # Diarization (разделение по ролям)
        # Используем HF_HOME для сохранения модели на диск E
        hf_home = os.getenv("HF_HOME")
        if hf_home:
            os.environ["HF_HOME"] = hf_home
        
        # Получаем токен HuggingFace (если установлен)
        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        
        # Получаем путь к моделям HuggingFace
        hf_home = os.getenv("HF_HOME", "/app/huggingface-cache")
        
        # Загрузка модели diarization через pyannote
        # ВАЖНО: Модель требует токен Hugging Face и принятия условий использования
        # Получить токен: https://huggingface.co/settings/tokens
        # Принять условия: https://hf.co/pyannote/speaker-diarization-3.1
        try:
            # Пробуем использовать WhisperX.DiarizationPipeline, если доступен
            if hasattr(whisperx, 'DiarizationPipeline'):
                print("Используется WhisperX.DiarizationPipeline...")
                if not hf_token:
                    print("⚠️  Токен Hugging Face не указан (HF_TOKEN или HUGGINGFACE_TOKEN)")
                    print("   Для использования WhisperX diarization нужен токен.")
                    print("   Получите токен: https://huggingface.co/settings/tokens")
                    print("   Примите условия: https://hf.co/pyannote/speaker-diarization-3.1")
                    print("   Добавьте токен в настройки Spaces как секретную переменную HF_TOKEN")
                    raise ValueError("HF_TOKEN не указан. Требуется для доступа к модели diarization.")
                
                diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=hf_token,
                    device=device
                )
                
                if diarize_model is None:
                    raise ValueError("Не удалось загрузить модель diarization. Проверьте токен и условия использования.")
                    
            else:
                # Используем pyannote.audio напрямую
                print("DiarizationPipeline недоступен в whisperx, используем pyannote.audio...")
                print(f"Путь к моделям: {hf_home}")
                
                if not hf_token:
                    print("⚠️  Токен Hugging Face не указан (HF_TOKEN или HUGGINGFACE_TOKEN)")
                    print("   Для использования pyannote.audio diarization нужен токен.")
                    print("   Получите токен: https://huggingface.co/settings/tokens")
                    print("   Примите условия: https://hf.co/pyannote/speaker-diarization-3.1")
                    raise ValueError("HF_TOKEN не указан. Требуется для доступа к модели diarization.")
                
                from pyannote.audio import Pipeline
                
                # Загружаем модель из Hugging Face
                diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token,
                    cache_dir=hf_home
                )
                
                if diarize_model is None:
                    raise ValueError("Не удалось загрузить модель diarization. Проверьте токен и условия использования.")
                
                if device == "cuda":
                    import torch
                    diarize_model = diarize_model.to(torch.device("cuda"))
                
                print("✓ Модель diarization загружена")
        except Exception as diarize_load_error:
            error_msg = str(diarize_load_error)
            print(f"❌ Ошибка при загрузке модели diarization: {error_msg}")
            if "HF_TOKEN" in error_msg or "token" in error_msg.lower() or "NoneType" in error_msg:
                print("\n" + "="*60)
                print("РЕШЕНИЕ ПРОБЛЕМЫ:")
                print("="*60)
                print("1. Получите токен Hugging Face:")
                print("   https://huggingface.co/settings/tokens")
                print("2. Примите условия использования модели:")
                print("   https://hf.co/pyannote/speaker-diarization-3.1")
                print("3. Добавьте токен в настройки Spaces:")
                print("   Settings → Secrets → Добавьте HF_TOKEN")
                print("="*60 + "\n")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"✓ Модель diarization загружена")
        
        # Выполнение diarization
        # Правильная передача параметров для pyannote.audio
        print(f"Выполняется diarization... (спикеров: {num_speakers if num_speakers else 'авто'})")
        
        # Определяем, какой тип модели используется
        # WhisperX.DiarizationPipeline имеет метод min_speakers/max_speakers
        # pyannote.audio Pipeline - это просто callable объект
        is_whisperx_pipeline = hasattr(diarize_model, 'min_speakers') or hasattr(diarize_model, '__class__') and 'DiarizationPipeline' in str(type(diarize_model))
        is_pyannote_pipeline = not is_whisperx_pipeline and hasattr(diarize_model, '__call__')
        
        if is_pyannote_pipeline:
            # Это pyannote.audio Pipeline - используем правильный API
            print("Используется pyannote.audio Pipeline API...")
            from pyannote.core import Annotation
            
            try:
                # Формируем входные данные для pyannote
                # pyannote.audio ожидает словарь с ключом "uri" и "audio" (путь к файлу или массив)
                diarize_input = {"uri": "audio", "audio": audio_path}
                if num_speakers:
                    diarize_input["num_speakers"] = num_speakers
                
                # Выполняем diarization
                print("Выполняется diarization через pyannote.audio...")
                diarization_result = diarize_model(diarize_input)
                
                # Конвертируем результат pyannote в формат для присваивания спикеров
                # pyannote возвращает Annotation объект
                diarize_segments_list = []
                
                if isinstance(diarization_result, Annotation):
                    # Это Annotation объект - используем itertracks правильно
                    # itertracks возвращает (segment, track, label)
                    try:
                        for segment, track, speaker in diarization_result.itertracks(yield_label=True):
                            diarize_segments_list.append({
                                "segment": {
                                    "start": float(segment.start),
                                    "end": float(segment.end)
                                },
                                "speaker": str(speaker)  # Убеждаемся, что speaker - строка
                            })
                    except Exception as iter_error:
                        # Если itertracks не работает, пробуем другой способ
                        print(f"⚠️  Ошибка при итерации через itertracks: {iter_error}")
                        print("Пробуем альтернативный способ...")
                        # Используем get_timeline и get_labels
                        timeline = diarization_result.get_timeline()
                        for segment in timeline:
                            labels = diarization_result.get_labels(segment)
                            speaker = str(list(labels)[0]) if labels else "SPEAKER_00"
                            diarize_segments_list.append({
                                "segment": {
                                    "start": float(segment.start),
                                    "end": float(segment.end)
                                },
                                "speaker": speaker
                            })
                elif isinstance(diarization_result, dict):
                    # Если это словарь (некоторые версии могут возвращать dict)
                    for seg in diarization_result.get("segments", []):
                        diarize_segments_list.append({
                            "segment": {
                                "start": seg.get("start", 0),
                                "end": seg.get("end", 0)
                            },
                            "speaker": str(seg.get("speaker", "SPEAKER_00"))
                        })
                else:
                    # Пробуем преобразовать в список другим способом
                    print(f"⚠️  Неожиданный тип результата diarization: {type(diarization_result)}")
                    # Пробуем использовать get_timeline если доступен
                    if hasattr(diarization_result, 'get_timeline'):
                        timeline = diarization_result.get_timeline()
                        for segment in timeline:
                            # Пробуем получить спикера для сегмента
                            labels = diarization_result.get_labels(segment)
                            speaker = list(labels)[0] if labels else "SPEAKER_00"
                            diarize_segments_list.append({
                                "segment": {
                                    "start": float(segment.start),
                                    "end": float(segment.end)
                                },
                                "speaker": str(speaker)
                            })
                    else:
                        raise ValueError(f"Не удалось обработать результат diarization типа {type(diarization_result)}")
                
                print(f"✓ Diarization завершена: найдено {len(diarize_segments_list)} сегментов спикеров")
                
                # Объединяем транскрипцию с diarization вручную
                print("Объединение транскрипции с diarization...")
                result = self._assign_speakers_manual(result, diarize_segments_list)
                print("✓ Спикеры успешно присвоены к сегментам транскрипции")
            except Exception as pyannote_error:
                error_msg = str(pyannote_error)
                print(f"❌ Ошибка при выполнении pyannote diarization: {error_msg}")
                import traceback
                traceback.print_exc()
                raise
        else:
            # Это WhisperX DiarizationPipeline - используем стандартный API
            print("Используется WhisperX DiarizationPipeline API...")
            try:
                # WhisperX DiarizationPipeline принимает путь к аудио файлу
                print(f"Выполняется diarization для файла: {audio_path}")
                diarize_segments = diarize_model(
                    audio_path,
                    min_speakers=num_speakers if num_speakers else None,
                    max_speakers=num_speakers if num_speakers else None
                )
                
                print(f"Результат diarization: тип={type(diarize_segments)}")
                if hasattr(diarize_segments, '__len__'):
                    print(f"  Длина результата: {len(diarize_segments)}")
                
                # Конвертируем результат в нужный формат
                diarize_segments_list = []
                from pyannote.core import Annotation
                import pandas as pd
                
                if isinstance(diarize_segments, pd.DataFrame):
                    # WhisperX DiarizationPipeline возвращает pandas DataFrame
                    print("Результат - pandas DataFrame")
                    print(f"  Колонки: {list(diarize_segments.columns)}")
                    print(f"  Первые строки:\n{diarize_segments.head()}")
                    
                    # DataFrame обычно содержит колонки: start, end, speaker
                    for _, row in diarize_segments.iterrows():
                        diarize_segments_list.append({
                            "segment": {
                                "start": float(row.get("start", row.get("start_time", 0))),
                                "end": float(row.get("end", row.get("end_time", 0)))
                            },
                            "speaker": str(row.get("speaker", row.get("label", "SPEAKER_00")))
                        })
                    print(f"  Обработано {len(diarize_segments_list)} сегментов из DataFrame")
                elif isinstance(diarize_segments, dict):
                    # Если это словарь с ключом "segments"
                    print("Результат - словарь")
                    segments = diarize_segments.get("segments", [])
                    print(f"  Найдено сегментов в словаре: {len(segments)}")
                    for seg in segments:
                        diarize_segments_list.append({
                            "segment": {
                                "start": seg.get("start", 0),
                                "end": seg.get("end", 0)
                            },
                            "speaker": str(seg.get("speaker", "SPEAKER_00"))
                        })
                elif isinstance(diarize_segments, Annotation):
                    # Если это Annotation объект
                    print("Результат - Annotation объект")
                    try:
                        # Пробуем использовать itertracks
                        for segment, track, speaker in diarize_segments.itertracks(yield_label=True):
                            diarize_segments_list.append({
                                "segment": {
                                    "start": float(segment.start),
                                    "end": float(segment.end)
                                },
                                "speaker": str(speaker)
                            })
                    except Exception as iter_error:
                        print(f"⚠️  Ошибка при итерации через itertracks: {iter_error}")
                        # Fallback: используем get_timeline
                        timeline = diarize_segments.get_timeline()
                        print(f"  Timeline содержит {len(timeline)} сегментов")
                        for segment in timeline:
                            labels = diarize_segments.get_labels(segment)
                            speaker = str(list(labels)[0]) if labels else "SPEAKER_00"
                            diarize_segments_list.append({
                                "segment": {
                                    "start": float(segment.start),
                                    "end": float(segment.end)
                                },
                                "speaker": speaker
                            })
                else:
                    # Пробуем преобразовать в список
                    print(f"Неожиданный тип результата: {type(diarize_segments)}")
                    # Если это итерируемый объект, пробуем преобразовать
                    try:
                        for item in diarize_segments:
                            if isinstance(item, dict):
                                diarize_segments_list.append({
                                    "segment": {
                                        "start": item.get("start", 0),
                                        "end": item.get("end", 0)
                                    },
                                    "speaker": str(item.get("speaker", "SPEAKER_00"))
                                })
                    except Exception as iter_error:
                        print(f"⚠️  Не удалось итерировать результат: {iter_error}")
                        import traceback
                        traceback.print_exc()
                
                print(f"✓ Diarization завершена: найдено {len(diarize_segments_list)} сегментов спикеров")
                
                if len(diarize_segments_list) == 0:
                    print("⚠️  Diarization не нашла сегментов спикеров!")
                    print("   Возможно, аудио слишком короткое или содержит только одного спикера")
                    print("   Используем простую diarization на основе пауз как fallback")
                    # Fallback на простую diarization
                    if SIMPLE_DIARIZATION_AVAILABLE:
                        return self._transcribe_with_simple_diarization(
                            audio_path, language, model, beam_size=5, best_of=5, speaker_names=speaker_names
                        )
                    else:
                        raise ValueError("Diarization не нашла спикеров и простая diarization недоступна")
                
                # Объединяем транскрипцию с diarization вручную
                print("Объединение транскрипции с diarization...")
                result = self._assign_speakers_manual(result, diarize_segments_list)
                print("✓ Спикеры успешно присвоены к сегментам транскрипции")
            except Exception as diarize_error:
                print(f"⚠️  Ошибка при выполнении diarization: {diarize_error}")
                import traceback
                traceback.print_exc()
                raise
        
        # Форматирование результата
        segments = []
        speakers_text = {}  # Группировка по спикерам
        
        for segment in result["segments"]:
            speaker = segment.get("speaker", "SPEAKER_00")
            seg_dict = {
                "id": len(segments),
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "speaker": speaker
            }
            segments.append(seg_dict)
            
            # Группировка текста по спикерам
            if speaker not in speakers_text:
                speakers_text[speaker] = []
            speakers_text[speaker].append(segment["text"].strip())
        
        # Формирование текста по спикерам
        speakers_output = {
            speaker: " ".join(texts)
            for speaker, texts in speakers_text.items()
        }
        
        # Формируем красивый текст с разделением по спикерам
        formatted_text_parts = []
        current_speaker = None
        current_text_parts = []
        
        for seg in segments:
            speaker = seg.get("speaker", "SPEAKER_00")
            text = seg.get("text", "").strip()
            
            if not text:
                continue
            
            if speaker != current_speaker:
                # Новый спикер - добавляем предыдущий текст
                if current_speaker and current_text_parts:
                    speaker_name = self._format_speaker_name(current_speaker, speaker_names)
                    formatted_text_parts.append(f"{speaker_name}: {' '.join(current_text_parts)}")
                    current_text_parts = []
                current_speaker = speaker
            
            current_text_parts.append(text)
        
        # Добавляем последнего спикера
        if current_speaker and current_text_parts:
            speaker_name = self._format_speaker_name(current_speaker, speaker_names)
            formatted_text_parts.append(f"{speaker_name}: {' '.join(current_text_parts)}")
        
        formatted_text = "\n\n".join(formatted_text_parts)
        
        return {
            "text": " ".join([seg["text"] for seg in segments]),  # Простой текст
            "formatted_text": formatted_text,  # Красивый текст с разделением по спикерам
            "language": result.get("language", "unknown"),
            "segments": segments,
            "speakers": speakers_output,  # Текст по каждому спикеру
            "num_speakers": len(speakers_output)
        }
    
    def _assign_speakers_manual(self, whisper_result: Dict, diarization_segments: List) -> Dict:
        """Вручную присваивает спикеров к сегментам транскрипции на основе временных меток"""
        # Создаем словарь спикеров по времени
        speaker_map = {}
        for seg in diarization_segments:
            segment = seg.get("segment", {})
            speaker = seg.get("speaker", "SPEAKER_00")
            start = segment.get("start", 0)
            end = segment.get("end", start)
            # Используем середину сегмента как ключ
            mid_time = (start + end) / 2
            speaker_map[mid_time] = speaker
        
        # Присваиваем спикеров к каждому сегменту транскрипции
        for segment in whisper_result.get("segments", []):
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", seg_start)
            seg_mid = (seg_start + seg_end) / 2
            
            # Находим ближайшего спикера
            closest_speaker = "SPEAKER_00"
            min_distance = float('inf')
            
            for time_key, speaker in speaker_map.items():
                distance = abs(time_key - seg_mid)
                if distance < min_distance:
                    min_distance = distance
                    closest_speaker = speaker
            
            # Присваиваем спикера к сегменту
            segment["speaker"] = closest_speaker
        
        return whisper_result
    
    def _transcribe_with_simple_diarization(
        self,
        audio_path: str,
        language: Optional[str],
        model: str,
        beam_size: int,
        best_of: int,
        speaker_names: Optional[List[str]] = None
    ) -> Dict:
        """Транскрипция с простым разделением по ролям на основе пауз (не требует дополнительных моделей)"""
        if not SIMPLE_DIARIZATION_AVAILABLE:
            raise ImportError("Простая diarization недоступна")
        
        # Стандартная транскрипция
        whisper_model = self.load_model(model)
        
        if FASTER_WHISPER_AVAILABLE:
            # Faster-Whisper API
            segments, info = whisper_model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                best_of=best_of,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            segments_list = []
            for segment in segments:
                segments_list.append({
                    "id": len(segments_list),
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })
        else:
            # Стандартный Whisper
            result = whisper_model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                beam_size=beam_size,
                best_of=best_of
            )
            
            segments_list = [
                {
                    "id": seg.get("id", i),
                    "start": seg.get("start", 0),
                    "end": seg.get("end", 0),
                    "text": seg.get("text", "").strip()
                }
                for i, seg in enumerate(result.get("segments", []))
            ]
            # Создаем объект info с языком для совместимости с Faster-Whisper API
            class Info:
                def __init__(self, lang):
                    self.language = lang
            info = Info(result.get("language", "unknown"))
        
        # Проверка на пустые сегменты
        if not segments_list:
            raise ValueError("Не удалось получить сегменты из аудио. Проверьте, что аудио содержит речь.")
        
        # Применяем простую diarization с очень чувствительным порогом
        # Используем агрессивный порог 0.3 сек + анализ паттернов вопрос-ответ
        segments_with_speakers = simple_diarization(segments_list, pause_threshold=0.3)
        
        # Подсчитываем количество уникальных спикеров для отладки
        unique_speakers = set(seg.get("speaker", "SPEAKER_00") for seg in segments_with_speakers)
        print(f"✓ Простая diarization применена: найдено {len(unique_speakers)} спикеров")
        print(f"  Спикеры: {sorted(unique_speakers)}")
        
        # Группируем по спикерам
        speakers_output = group_by_speakers(segments_with_speakers)
        
        # Формируем полный текст (простой вариант без меток спикеров)
        full_text = " ".join([seg.get("text", "") for seg in segments_with_speakers if seg.get("text")])
        
        # Формируем красивый текст с разделением по спикерам
        formatted_text_parts = []
        current_speaker = None
        current_text_parts = []
        
        for seg in segments_with_speakers:
            speaker = seg.get("speaker", "SPEAKER_00")
            text = seg.get("text", "").strip()
            
            if not text:
                continue
            
            if speaker != current_speaker:
                # Новый спикер - добавляем предыдущий текст
                if current_speaker and current_text_parts:
                    speaker_name = self._format_speaker_name(current_speaker, speaker_names)
                    formatted_text_parts.append(f"{speaker_name}: {' '.join(current_text_parts)}")
                    current_text_parts = []
                current_speaker = speaker
            
            current_text_parts.append(text)
        
        # Добавляем последнего спикера
        if current_speaker and current_text_parts:
            speaker_name = self._format_speaker_name(current_speaker, speaker_names)
            formatted_text_parts.append(f"{speaker_name}: {' '.join(current_text_parts)}")
        
        formatted_text = "\n\n".join(formatted_text_parts)
        
        return {
            "text": full_text,  # Простой текст без меток
            "formatted_text": formatted_text,  # Красивый текст с разделением по спикерам
            "language": info.language,
            "segments": segments_with_speakers,
            "speakers": speakers_output,
            "num_speakers": len(speakers_output)
        }
    
    def generate_subtitles(self, transcription_result: Dict, format: str = "srt", include_speakers: bool = False) -> str:
        """Генерирует субтитры с опциональным указанием спикеров"""
        segments = transcription_result.get("segments", [])
        
        if format.lower() == "srt":
            return self._generate_srt(segments, include_speakers)
        elif format.lower() == "vtt":
            return self._generate_vtt(segments, include_speakers)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
    
    def _generate_srt(self, segments: List[Dict], include_speakers: bool = False) -> str:
        """Генерирует SRT с опциональными метками спикеров"""
        srt_lines = []
        for seg in segments:
            idx = seg.get("id", 0) + 1
            start = self._format_timestamp(seg.get("start", 0))
            end = self._format_timestamp(seg.get("end", 0))
            text = seg.get("text", "")
            
            # Добавляем метку спикера, если есть
            if include_speakers and "speaker" in seg:
                text = f"[{seg['speaker']}] {text}"
            
            srt_lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
        
        return "\n".join(srt_lines)
    
    def _format_speaker_name(self, speaker: str, speaker_names: Optional[List[str]] = None) -> str:
        """Форматирует имя спикера для красивого отображения"""
        # Если переданы имена спикеров, используем их
        if speaker_names and len(speaker_names) > 0:
            if speaker.startswith("SPEAKER_"):
                speaker_num = speaker.replace("SPEAKER_", "")
                try:
                    num = int(speaker_num)
                    if 0 <= num < len(speaker_names):
                        return speaker_names[num]
                except:
                    pass
        
        # Преобразуем SPEAKER_00 в более читаемый формат
        if speaker.startswith("SPEAKER_"):
            speaker_num = speaker.replace("SPEAKER_", "")
            # Используем простую нумерацию (можно улучшить с помощью ML для определения имен)
            try:
                num = int(speaker_num)
                if num == 0:
                    return "Спикер 1"
                elif num == 1:
                    return "Спикер 2"
                else:
                    return f"Спикер {num + 1}"
            except:
                return f"Спикер {speaker_num}"
        return speaker
    
    def _generate_vtt(self, segments: List[Dict], include_speakers: bool = False) -> str:
        """Генерирует VTT с опциональными метками спикеров"""
        vtt_lines = ["WEBVTT\n"]
        for seg in segments:
            start = self._format_timestamp_vtt(seg.get("start", 0))
            end = self._format_timestamp_vtt(seg.get("end", 0))
            text = seg.get("text", "")
            
            # Добавляем метку спикера, если есть
            if include_speakers and "speaker" in seg:
                text = f"<v {seg['speaker']}>{text}</v>"
            
            vtt_lines.append(f"{start} --> {end}\n{text}\n")
        
        return "\n".join(vtt_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Форматирует время для SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_timestamp_vtt(self, seconds: float) -> str:
        """Форматирует время для VTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

