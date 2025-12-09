# Ручная загрузка модели Faster-Whisper через браузер

## 🔗 Прямые ссылки на модели

### Medium модель (рекомендуется):
**https://huggingface.co/guillaumekln/faster-whisper-medium**

### Другие модели:
- **Base:** https://huggingface.co/guillaumekln/faster-whisper-base
- **Small:** https://huggingface.co/guillaumekln/faster-whisper-small  
- **Large:** https://huggingface.co/guillaumekln/faster-whisper-large-v2
- **Large-v3:** https://huggingface.co/guillaumekln/faster-whisper-large-v3

## 📥 Как скачать

### ⚠️ Важно: Файл model.bin в Git LFS!

Файл `model.bin` (1.53 GB) имеет тег **"xet"** - это означает, что он хранится в Git LFS (Large File Storage). Его нельзя скачать обычной кнопкой.

### Способ 1: Скачать через HuggingFace CLI (рекомендуется)

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Установите huggingface-hub (если еще не установлен)
pip install huggingface-hub

# Скачайте модель
huggingface-cli download guillaumekln/faster-whisper-medium --local-dir "E:\whisper-models\medium"
```

### Способ 2: Скачать через Python скрипт

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from huggingface_hub import snapshot_download; snapshot_download('guillaumekln/faster-whisper-medium', local_dir='E:/whisper-models/medium')"
```

### Способ 3: Использовать Git LFS (если установлен Git)

```powershell
# Установите Git LFS: https://git-lfs.github.com/
# Затем клонируйте репозиторий

# Если директория уже существует, удалите её или используйте другое имя:
cd E:\whisper-models

# Вариант A: Удалить существующую директорию и клонировать заново
Remove-Item -Recurse -Force medium
git lfs install
git clone https://huggingface.co/guillaumekln/faster-whisper-medium medium

# Вариант B: Клонировать в другую папку, потом переименовать
git lfs install
git clone https://huggingface.co/guillaumekln/faster-whisper-medium medium-temp
# Проверьте содержимое, затем переместите файлы в medium\
```

**⚠️ Если директория уже существует и содержит файлы:**
- Проверьте, что в ней есть (может быть уже скачано)
- Если файлы неполные, удалите директорию и клонируйте заново
- Если файлы есть, просто обновите через `git pull`:
  ```powershell
  cd medium
  git lfs pull
  ```

### Способ 4: Скачать через браузер (только маленькие файлы)

1. Откройте ссылку: https://huggingface.co/guillaumekln/faster-whisper-medium
2. Перейдите на вкладку **"Files and versions"**
3. Скачайте файлы по отдельности:
   - ✅ `config.json` - скачается нормально
   - ✅ `tokenizer.json` - скачается нормально  
   - ✅ `vocabulary.txt` - скачается нормально
   - ❌ `model.bin` - **НЕ скачается** через браузер (нужен Git LFS или CLI)

**Для model.bin используйте один из способов выше!**

## 📁 Куда разместить

После скачивания распакуйте архив и скопируйте содержимое в:

```
E:\whisper-models\medium\
```

**Структура должна быть:**
```
E:\whisper-models\
└── medium\
    ├── config.json
    ├── model.bin
    ├── tokenizer.json
    ├── vocabulary.txt
    └── ... (другие файлы)
```

## ✅ Проверка

После размещения файлов перезапустите сервер - модель должна загрузиться без скачивания.

