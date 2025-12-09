"""
Конфигурация приложения
"""
import os
from pathlib import Path
from typing import Optional

# Путь к кэшу моделей Whisper
# Можно установить через переменную окружения WHISPER_CACHE_DIR
# По умолчанию: /app/models (для Docker) или E:\whisper-models (для Windows)
WHISPER_CACHE_DIR: Optional[str] = os.getenv(
    "WHISPER_CACHE_DIR",
    "/app/models" if os.path.exists("/app") else (
        "E:\\whisper-models" if os.path.exists("E:\\") else None
    )
)

# Путь к кэшу HuggingFace (для моделей diarization)
# WhisperX использует модели из HuggingFace
# По умолчанию: /app/huggingface-cache (для Docker) или E:\models\huggingface (для Windows)
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

