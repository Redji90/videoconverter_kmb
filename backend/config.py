"""
Конфигурация приложения
"""
import os
from pathlib import Path
from typing import Optional

# Путь к кэшу моделей Whisper
# Можно установить через переменную окружения WHISPER_CACHE_DIR
# Приоритет: переменная окружения > /app/models (Docker/Spaces) > E:\whisper-models (Windows) > системный кэш
WHISPER_CACHE_DIR: Optional[str] = os.getenv(
    "WHISPER_CACHE_DIR",
    "/app/models" if os.path.exists("/app") else (
        "E:\\whisper-models" if os.path.exists("E:\\") else None
    )
)

# Путь к кэшу HuggingFace (для моделей diarization)
# WhisperX использует модели из HuggingFace
# Приоритет: переменная окружения > /app/huggingface-cache (Docker/Spaces) > E:\models\huggingface (Windows) > системный кэш
HF_HOME: Optional[str] = os.getenv(
    "HF_HOME",
    "/app/huggingface-cache" if os.path.exists("/app") else (
        "E:\\models\\huggingface" if os.path.exists("E:\\") else None
    )
)

# Создаем директории, если указаны кастомные пути
if WHISPER_CACHE_DIR:
    cache_path = Path(WHISPER_CACHE_DIR)
    cache_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Модели Whisper будут сохраняться в: {cache_path}")

if HF_HOME:
    hf_path = Path(HF_HOME)
    hf_path.mkdir(parents=True, exist_ok=True)
    # Устанавливаем переменную окружения для HuggingFace
    os.environ["HF_HOME"] = str(hf_path)
    print(f"✓ Модели HuggingFace (diarization) будут сохраняться в: {hf_path}")

