from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
from pathlib import Path
import shutil
import time
import warnings

# Фильтрация предупреждений Whisper о FP16 на CPU (это нормальное поведение)
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead", category=UserWarning)

# ВАЖНО: Сначала устанавливаем WHISPER_CACHE_DIR из config
# Это нужно сделать ДО импорта сервисов, так как Whisper использует
# этот путь при импорте модуля
try:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import WHISPER_CACHE_DIR as CONFIG_WHISPER_CACHE_DIR
    if CONFIG_WHISPER_CACHE_DIR and "WHISPER_CACHE_DIR" not in os.environ:
        os.environ["WHISPER_CACHE_DIR"] = CONFIG_WHISPER_CACHE_DIR
except ImportError:
    pass

from app.services.video_processor import VideoProcessor
from app.services.speech_recognition import SpeechRecognitionService

# Попытка импорта оптимизированного сервиса
try:
    from app.services.speech_recognition_optimized import OptimizedSpeechRecognitionService
    OPTIMIZED_AVAILABLE = True
except ImportError:
    OPTIMIZED_AVAILABLE = False

# Импорт конфигурации (опционально, можно использовать переменные окружения напрямую)
# Примечание: WHISPER_CACHE_DIR теперь устанавливается выше, ДО импорта сервисов
try:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import WHISPER_CACHE_DIR
except ImportError:
    WHISPER_CACHE_DIR = None

app = FastAPI(title="Video to Text Converter", version="1.0.0")

# Добавляем маршрут для статики (frontend) если развернуто на Spaces
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    @app.get("/")
    async def read_root():
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": "Video to Text Converter API", "status": "running"}

# CORS middleware для работы с frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники для разработки
    allow_credentials=False,  # Отключаем credentials для разрешения всех источников
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware для логирования всех запросов
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import time
        start = time.time()
        print(f"\n{'='*60}")
        print(f">>> ВХОДЯЩИЙ ЗАПРОС: {request.method} {request.url.path}")
        print(f"Origin: {request.headers.get('origin', 'не указан')}")
        print(f"Content-Type: {request.headers.get('content-type', 'не указан')}")
        print(f"Content-Length: {request.headers.get('content-length', 'не указан')}")
        
        try:
            response = await call_next(request)
            elapsed = time.time() - start
            print(f"<<< ОТВЕТ: {response.status_code} (за {elapsed:.2f} сек)")
            print(f"{'='*60}\n")
            return response
        except Exception as e:
            elapsed = time.time() - start
            print(f"!!! ОШИБКА В MIDDLEWARE: {e} (за {elapsed:.2f} сек)")
            print(f"{'='*60}\n")
            raise

app.add_middleware(LoggingMiddleware)

# Инициализация сервисов
video_processor = VideoProcessor()

# Получение пути к кэшу моделей
# Приоритет: переменная окружения > config.py > системный кэш
whisper_cache_dir = os.getenv("WHISPER_CACHE_DIR", WHISPER_CACHE_DIR)

# ВАЖНО: Устанавливаем WHISPER_CACHE_DIR ДО импорта сервисов
# Whisper использует этот путь при импорте модуля
if whisper_cache_dir:
    os.environ["WHISPER_CACHE_DIR"] = whisper_cache_dir
    print(f"✓ WHISPER_CACHE_DIR установлен: {whisper_cache_dir}")
    
    # Проверка наличия модели medium.pt
    cache_path = Path(whisper_cache_dir)
    model_file = cache_path / "medium.pt"
    if model_file.exists():
        size_gb = model_file.stat().st_size / (1024 * 1024 * 1024)
        print(f"✓ Модель medium.pt найдена ({size_gb:.2f} GB)")

# Установка пути для HuggingFace (для моделей diarization)
try:
    from config import HF_HOME
    if HF_HOME:
        os.environ["HF_HOME"] = HF_HOME
        print(f"✓ Путь к моделям HuggingFace: {HF_HOME}")
except ImportError:
    pass

# Также можно установить через переменную окружения напрямую
hf_home = os.getenv("HF_HOME")
if hf_home:
    os.environ["HF_HOME"] = hf_home

# Использование оптимизированного сервиса, если доступен
use_gpu = os.getenv("USE_GPU", "false").lower() == "true"
if OPTIMIZED_AVAILABLE:
    speech_service = OptimizedSpeechRecognitionService(
        cache_dir=whisper_cache_dir,
        use_gpu=use_gpu,
        device="auto"
    )
    print("✓ Используется оптимизированный сервис распознавания")
else:
    speech_service = SpeechRecognitionService(cache_dir=whisper_cache_dir)
    print("⚠ Используется стандартный сервис. Для ускорения установите: pip install faster-whisper")

# Корневой маршрут уже определен выше для статики
# Если статика не найдена, этот маршрут будет работать
@app.get("/api")
async def api_root():
    return {"message": "Video to Text Converter API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/test")
async def test():
    print(">>> ТЕСТОВЫЙ ЗАПРОС ПОЛУЧЕН!")
    return {"message": "Backend работает!", "timestamp": time.time()}

@app.post("/api/convert")
async def convert_video_to_text(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("base"),
    beam_size: int = Form(5),
    enable_diarization: bool = Form(False),
    num_speakers: Optional[int] = Form(None)
):
    """
    Конвертирует видео в текст
    
    Parameters:
    - file: видео файл
    - language: язык распознавания (код ISO, например 'ru', 'en', 'auto')
    - model: модель Whisper (tiny, base, small, medium, large)
    """
    import time
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"=== НОВЫЙ ЗАПРОС НА КОНВЕРТАЦИЮ ===")
    print(f"Файл: {file.filename}")
    print(f"Размер: {file.size if hasattr(file, 'size') else 'неизвестно'} байт")
    print(f"Настройки: язык={language}, модель={model}, beam_size={beam_size}")
    print(f"Diarization: {enable_diarization}, спикеров={num_speakers}")
    print(f"{'='*60}\n")
    
    try:
        # Сохранение временного файла (используем более надежный способ для больших файлов)
        suffix = Path(file.filename).suffix if file.filename else ".mp4"
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name
        
        print(f"[1/4] Сохранение файла: {tmp_path}")
        print(f"Начало чтения файла из запроса...")
        save_start = time.time()
        
        # Сохраняем файл по частям для больших файлов (асинхронно)
        bytes_written = 0
        chunk_size = 1024 * 1024  # 1 MB chunks
        with open(tmp_path, "wb") as tmp_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                tmp_file.write(chunk)
                bytes_written += len(chunk)
                if bytes_written % (10 * 1024 * 1024) == 0:  # Каждые 10 MB
                    print(f"  Записано: {bytes_written / 1024 / 1024:.1f} MB...")
        
        print(f"  Всего записано: {bytes_written / 1024 / 1024:.1f} MB")
        
        file_size = os.path.getsize(tmp_path)
        save_time = time.time() - save_start
        print(f"[1/4] Файл сохранен: {file_size / 1024 / 1024:.2f} MB за {save_time:.2f} сек")
        
        try:
            # Извлечение аудио из видео
            print(f"[2/4] Извлечение аудио из видео...")
            extract_start = time.time()
            audio_path = video_processor.extract_audio(tmp_path)
            extract_time = time.time() - extract_start
            audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            print(f"[2/4] Аудио извлечено: {audio_size / 1024 / 1024:.2f} MB за {extract_time:.2f} сек")
            
            # Распознавание речи
            print(f"[3/4] Начало распознавания речи (модель: {model})...")
            transcribe_start = time.time()
            
            if hasattr(speech_service, 'transcribe'):
                # Оптимизированный сервис
                print(f"Используется оптимизированный сервис")
                try:
                    result = speech_service.transcribe(
                        audio_path=audio_path,
                        language=language if language != "auto" else None,
                        model=model,
                        beam_size=beam_size,
                        enable_diarization=enable_diarization,
                        num_speakers=num_speakers
                    )
                except Exception as e:
                    print(f"❌ Ошибка при транскрипции: {e}")
                    import traceback
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Ошибка транскрипции: {str(e)}")
            else:
                # Стандартный сервис
                print(f"Используется стандартный сервис")
                try:
                    result = speech_service.transcribe(
                        audio_path=audio_path,
                        language=language if language != "auto" else None,
                        model=model
                    )
                except Exception as e:
                    print(f"❌ Ошибка при транскрипции: {e}")
                    import traceback
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=f"Ошибка транскрипции: {str(e)}")
            
            transcribe_time = time.time() - transcribe_start
            print(f"[3/4] Распознавание завершено за {transcribe_time:.2f} сек")
            print(f"Результат: {len(result.get('text', ''))} символов, {len(result.get('segments', []))} сегментов")
            
            response_data = {
                "success": True,
                "text": result["text"],
                "segments": result.get("segments", []),
                "language": result.get("language", "unknown")
            }
            
            # Добавляем информацию о спикерах, если есть
            if "speakers" in result:
                response_data["speakers"] = result["speakers"]
                response_data["num_speakers"] = result.get("num_speakers", 0)
            
            total_time = time.time() - start_time
            print(f"[4/4] Формирование ответа...")
            print(f"{'='*60}")
            print(f"=== КОНВЕРТАЦИЯ ЗАВЕРШЕНА УСПЕШНО ===")
            print(f"Общее время: {total_time:.2f} сек ({total_time/60:.2f} мин)")
            print(f"Текст: {len(response_data['text'])} символов")
            print(f"Сегментов: {len(response_data['segments'])}")
            print(f"{'='*60}\n")
            
            return JSONResponse(content=response_data)
        
        finally:
            # Очистка временных файлов
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/convert-with-subtitles")
async def convert_with_subtitles(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("base"),
    format: str = Form("srt"),  # srt или vtt
    beam_size: int = Form(5),
    enable_diarization: bool = Form(False),
    num_speakers: Optional[int] = Form(None),
    include_speakers: bool = Form(False)
):
    """
    Конвертирует видео в текст с субтитрами
    """
    try:
        # Сохранение временного файла (используем более надежный способ для больших файлов)
        suffix = Path(file.filename).suffix if file.filename else ".mp4"
        tmp_path = tempfile.NamedTemporaryFile(delete=False, suffix=suffix).name
        
        # Сохраняем файл по частям для больших файлов
        with open(tmp_path, "wb") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
        
        try:
            audio_path = video_processor.extract_audio(tmp_path)
            
            # Распознавание речи
            if hasattr(speech_service, 'transcribe'):
                # Оптимизированный сервис
                result = speech_service.transcribe(
                    audio_path=audio_path,
                    language=language if language != "auto" else None,
                    model=model,
                    beam_size=beam_size,
                    enable_diarization=enable_diarization,
                    num_speakers=num_speakers
                )
            else:
                # Стандартный сервис
                result = speech_service.transcribe(
                    audio_path=audio_path,
                    language=language if language != "auto" else None,
                    model=model
                )
            
            # Генерация субтитров
            if hasattr(speech_service, 'generate_subtitles'):
                subtitles = speech_service.generate_subtitles(
                    result, 
                    format=format,
                    include_speakers=include_speakers and enable_diarization
                )
            else:
                subtitles = speech_service.generate_subtitles(result, format=format)
            
            response_data = {
                "success": True,
                "text": result["text"],
                "subtitles": subtitles,
                "format": format,
                "language": result.get("language", "unknown")
            }
            
            # Добавляем информацию о спикерах, если есть
            if "speakers" in result:
                response_data["speakers"] = result["speakers"]
                response_data["num_speakers"] = result.get("num_speakers", 0)
            
            return JSONResponse(content=response_data)
        
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

