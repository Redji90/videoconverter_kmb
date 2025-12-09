# Решение проблемы с зависанием загрузки XET файлов

## 🔍 Проблема

XET файлы на Windows часто вызывают зависание загрузки. Это известная проблема:
- [Issue #399](https://github.com/huggingface/xet-core/issues/399) - Cannot Download XET Files
- [Issue #446](https://github.com/huggingface/xet-core/issues/446) - xet too broken on windows: downloading hangs
- [Issue #409](https://github.com/huggingface/xet-core/issues/409) - Download stucks at 99%
- [Issue #581](https://github.com/huggingface/xet-core/issues/581) - Increased failure rate with xet

## ✅ Решение 1: Отключить XET (рекомендуется)

### Вариант A: Удалить hf-xet

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1
pip uninstall hf-xet -y
```

После этого загрузка будет использовать обычный HTTPS вместо XET.

### Вариант B: Отключить через переменную окружения

```powershell
$env:HF_XET_DISABLE="1"
cd C:\prj\converter\backend
.\venv\Scripts\python.exe download_faster_whisper_model.py base
```

## ✅ Решение 2: Использовать обновленный скрипт

Я обновил скрипт `download_faster_whisper_model.py` - он теперь автоматически отключает XET.

Просто запустите:

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\python.exe download_faster_whisper_model.py base
```

## ✅ Решение 3: Использовать стандартный Whisper (самое простое)

Если проблемы продолжаются:

```powershell
cd C:\prj\converter\backend
.\venv\Scripts\Activate.ps1
pip uninstall faster-whisper hf-xet -y
```

Тогда будет использоваться ваш `medium.pt` - ничего скачивать не нужно!

## 📋 Что проверить

1. ✅ У вас установлен `hf-xet 1.2.0` - это может вызывать проблемы
2. ✅ Скрипт теперь автоматически отключает XET
3. ✅ Можно удалить hf-xet для полного отключения

## 🚀 Рекомендация

**Самый простой способ:**
1. Удалите hf-xet: `pip uninstall hf-xet -y`
2. Запустите скрипт загрузки снова
3. Или используйте стандартный Whisper с вашим `medium.pt`

