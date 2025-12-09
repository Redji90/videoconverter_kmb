# Как скачать файлы с тегом "xet" (Git LFS) через браузер

Файлы с тегом **"xet"** хранятся в Git LFS (Large File Storage) и **нельзя скачать** обычной кнопкой в браузере.

## ❌ Что НЕ работает

- ❌ Обычная кнопка "Download" в браузере
- ❌ Прямая ссылка на файл
- ❌ Сохранение через "Сохранить как"

## ✅ Что работает

### Способ 1: HuggingFace CLI (самый простой) ⭐

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1

# Установите huggingface-hub (если еще не установлен)
pip install huggingface-hub

# Скачайте всю модель (включая model.bin)
python -c "from huggingface_hub import snapshot_download; snapshot_download('guillaumekln/faster-whisper-base', local_dir='E:/whisper-models/base')"
```

### Способ 2: Использовать готовый скрипт

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\python.exe download_faster_whisper_model.py base
```

### Способ 3: Git LFS (если установлен Git)

```powershell
# 1. Установите Git LFS: https://git-lfs.github.com/

# 2. Инициализируйте Git LFS
git lfs install

# 3. Клонируйте репозиторий
cd E:\whisper-models
git clone https://huggingface.co/guillaumekln/faster-whisper-base base

# 4. Скачайте LFS файлы
cd base
git lfs pull
```

### Способ 4: Скачать через Python скрипт напрямую

Создайте файл `download_model.py`:

```python
from huggingface_hub import hf_hub_download
from pathlib import Path

# Скачать только model.bin
model_path = hf_hub_download(
    repo_id="guillaumekln/faster-whisper-base",
    filename="model.bin",
    local_dir="E:/whisper-models/base"
)
print(f"Скачано: {model_path}")
```

Запустите:
```powershell
python download_model.py
```

## 🌐 Через браузер (частично)

Через браузер можно скачать только **маленькие файлы**:

1. ✅ `config.json` - скачается нормально
2. ✅ `tokenizer.json` - скачается нормально  
3. ✅ `vocabulary.txt` - скачается нормально
4. ❌ `model.bin` - **НЕ скачается** (нужен Git LFS или CLI)

**Но это не поможет** - без `model.bin` модель не будет работать!

## 💡 Рекомендация

**Используйте Способ 1 (HuggingFace CLI)** - это самый надежный способ:

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1
python -c "from huggingface_hub import snapshot_download; snapshot_download('guillaumekln/faster-whisper-base', local_dir='E:/whisper-models/base')"
```

Это скачает **все файлы**, включая `model.bin` через правильный API.

## 🔍 Почему нельзя через браузер?

Git LFS файлы хранятся на отдельном сервере и требуют специального протокола для скачивания. Обычный HTTP-запрос не работает - нужен либо Git LFS клиент, либо HuggingFace API.

## ⚡ Быстрое решение

Если скачивание не работает, используйте стандартный Whisper:

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1
pip uninstall faster-whisper -y
```

Тогда будет использоваться ваш `medium.pt` - ничего скачивать не нужно!


