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
            print(f"Загрузка модели: {model_name}")
            
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
                
                self.models[model_name] = WhisperModel(
                    model_name,
                    device=self.device,
                    compute_type="float16" if self.device == "cuda" else "int8",
                    download_root=download_path
                )
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
                self.models[model_name] = whisper.load_model(model_name)
            
            print(f"✓ Модель {model_name} загружена")
        return self.models[model_name]
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        model: str = "base",
        beam_size: int = 5,
        best_of: int = 5,
        enable_diarization: bool = False,
        num_speakers: Optional[int] = None
    ) -> Dict:
        """
        Распознает речь с опциональным разделением по ролям
        
        Args:
            audio_path: путь к аудио
            language: код языка
            model: модель Whisper
            beam_size: размер луча (меньше = быстрее, но менее точно)
            best_of: количество попыток (меньше = быстрее)
            enable_diarization: включить разделение по ролям
            num_speakers: количество спикеров (None = автоопределение)
        
        Returns:
            словарь с результатами
        """
        # Diarization: сначала пробуем WhisperX, если недоступен - используем простую эвристику
        if enable_diarization:
            if WHISPERX_AVAILABLE:
                try:
                    return self._transcribe_with_diarization(
                        audio_path, language, model, num_speakers
                    )
                except Exception as e:
                    print(f"⚠️  WhisperX diarization не удалось: {e}")
                    print("   Используем простую diarization на основе пауз")
                    # Fallback на простую diarization
                    if SIMPLE_DIARIZATION_AVAILABLE:
                        try:
                            return self._transcribe_with_simple_diarization(
                                audio_path, language, model, beam_size, best_of
                            )
                        except Exception as e2:
                            print(f"❌ Простая diarization также не удалась: {e2}")
                            print("   Продолжаем без diarization")
                            # Продолжаем с обычной транскрипцией
                    else:
                        print("   Простая diarization недоступна - продолжаем без разделения по ролям")
            elif SIMPLE_DIARIZATION_AVAILABLE:
                # Используем простую diarization, если WhisperX не установлен
                try:
                    return self._transcribe_with_simple_diarization(
                        audio_path, language, model, beam_size, best_of
                    )
                except Exception as e:
                    print(f"❌ Простая diarization не удалась: {e}")
                    print("   Продолжаем без diarization")
                    # Продолжаем с обычной транскрипцией
        
        # Стандартная транскрипция (быстрее)
        whisper_model = self.load_model(model)
        
        if FASTER_WHISPER_AVAILABLE:
            # Faster-Whisper API
            segments, info = whisper_model.transcribe(
                audio_path,
                language=language,
                beam_size=beam_size,
                best_of=best_of,
                vad_filter=True,  # Voice Activity Detection для ускорения
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
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
            
            return {
                "text": " ".join(full_text_parts),
                "language": info.language,
                "segments": segments_list
            }
        else:
            # Стандартный Whisper
            result = whisper_model.transcribe(
                audio_path,
                language=language,
                task="transcribe",
                beam_size=beam_size,
                best_of=best_of
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
    
    def _transcribe_with_diarization(
        self,
        audio_path: str,
        language: Optional[str],
        model: str,
        num_speakers: Optional[int]
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
        
        # Загружаем модель через WhisperX (возвращает Faster-Whisper модель)
        # Примечание: WhisperX может загружать модель заново, если не найдет в нужном формате
        # Это нормально при первом использовании diarization
        print(f"Загрузка модели Whisper через WhisperX: {model} (устройство: {device})")
        whisper_model = whisperx.load_model(
            model, 
            device, 
            compute_type="float16" if device == "cuda" else "int8",
            download_root=str(self.cache_dir) if self.cache_dir else None
        )
        print(f"Модель Whisper {model} загружена через WhisperX")
        
        # Загрузка аудио
        audio = whisperx.load_audio(audio_path)
        
        # Транскрипция через Faster-Whisper модель (whisper_model.transcribe, а не whisperx.transcribe)
        print("Выполняется транскрипция...")
        result = whisper_model.transcribe(audio, language=language)
        
        # WhisperX требует дополнительного выравнивания для точного присваивания слов
        # Загружаем модель выравнивания
        try:
            print("Выполняется выравнивание слов...")
            model_a, metadata = whisperx.load_align_model(language_code=result.get("language", "ru"), device=device)
            result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)
        except Exception as align_error:
            print(f"⚠️  Ошибка при выравнивании: {align_error}")
            print("Продолжаем без выравнивания...")
        
        # Diarization (разделение по ролям)
        # Используем HF_HOME для сохранения модели на диск E
        hf_home = os.getenv("HF_HOME")
        if hf_home:
            os.environ["HF_HOME"] = hf_home
        
        # Получаем токен HuggingFace (если установлен)
        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        
        # Получаем путь к моделям HuggingFace
        hf_home = os.getenv("HF_HOME", "E:\\models\\huggingface")
        
        # Загрузка модели diarization через pyannote (используем реальную модель, не ручное сопоставление)
        # Модели находятся в E:\models\huggingface
        try:
            # Пробуем использовать WhisperX.DiarizationPipeline, если доступен
            if hasattr(whisperx, 'DiarizationPipeline'):
                print("Используется WhisperX.DiarizationPipeline...")
                diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=hf_token,
                    device=device
                )
            else:
                # Используем pyannote.audio напрямую (модели уже скачаны)
                print("DiarizationPipeline недоступен в whisperx, используем pyannote.audio...")
                print(f"Путь к моделям: {hf_home}")
                from pyannote.audio import Pipeline
                
                # Загружаем модель из локального кэша
                # Pyannote автоматически найдет модели в HF_HOME
                diarize_model = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token,
                    cache_dir=hf_home  # Явно указываем путь к кэшу
                )
                if device == "cuda":
                    import torch
                    diarize_model = diarize_model.to(torch.device("cuda"))
                
                print("✓ Модель diarization загружена из локального кэша")
        except Exception as diarize_load_error:
            print(f"❌ Ошибка при загрузке модели diarization: {diarize_load_error}")
            import traceback
            traceback.print_exc()
            raise
        
        print(f"✓ Модель diarization загружена")
        
        # Выполнение diarization
        # Правильная передача параметров для pyannote.audio
        print(f"Выполняется diarization... (спикеров: {num_speakers if num_speakers else 'авто'})")
        
        # Определяем, какой тип модели используется
        is_pyannote_pipeline = hasattr(diarize_model, '__call__') and not hasattr(diarize_model, 'min_speakers')
        
        if is_pyannote_pipeline:
            # Это pyannote.audio Pipeline - используем правильный API
            print("Используется pyannote.audio Pipeline API...")
            from pyannote.core import Annotation
            
            # Формируем входные данные для pyannote
            diarize_input = {"uri": "audio", "audio": audio_path}
            if num_speakers:
                diarize_input["num_speakers"] = num_speakers
            
            # Выполняем diarization
            diarization = diarize_model(diarize_input)
            
            # Конвертируем результат pyannote в формат для WhisperX
            # pyannote возвращает Annotation, нужно преобразовать в список сегментов
            # Формат для whisperx.assign_word_speakers: список словарей с ключами "segment" и "speaker"
            diarize_segments_list = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                diarize_segments_list.append({
                    "segment": {
                        "start": float(turn.start),
                        "end": float(turn.end)
                    },
                    "speaker": speaker
                })
            
            print(f"✓ Diarization завершена: найдено {len(diarize_segments_list)} сегментов спикеров")
            
            # Используем WhisperX assign_word_speakers для точного сопоставления на уровне слов
            # Это более точный метод, чем ручное сопоставление по временным меткам
            try:
                print("Объединение транскрипции с diarization через WhisperX...")
                result = whisperx.assign_word_speakers(diarize_segments_list, result)
                print("✓ Спикеры успешно присвоены к словам транскрипции")
            except Exception as assign_error:
                print(f"⚠️  Ошибка при объединении через WhisperX: {assign_error}")
                print("Используем ручное присваивание спикеров (менее точное)...")
                result = self._assign_speakers_manual(result, diarize_segments_list)
        else:
            # Это WhisperX DiarizationPipeline - используем стандартный API
            print("Используется WhisperX DiarizationPipeline API...")
            diarize_segments = diarize_model(
                audio_path,
                min_speakers=num_speakers if num_speakers else None,
                max_speakers=num_speakers if num_speakers else None
            )
            
            # Объединение транскрипции с diarization
            result = whisperx.assign_word_speakers(diarize_segments, result)
        
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
        
        return {
            "text": " ".join([seg["text"] for seg in segments]),
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
        best_of: int
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
        
        # Применяем простую diarization
        segments_with_speakers = simple_diarization(segments_list, pause_threshold=1.0)
        
        # Группируем по спикерам
        speakers_output = group_by_speakers(segments_with_speakers)
        
        # Формируем полный текст
        full_text = " ".join([seg.get("text", "") for seg in segments_with_speakers if seg.get("text")])
        
        return {
            "text": full_text,
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

