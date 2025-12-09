# Руководство по переносу моделей на диск E

## Быстрый способ (автоматический):

```powershell
cd C:\prj\converter\backend
.\move_models_to_disk_e.ps1
```

Скрипт:
- Скопирует все модели из `C:\Users\Lenovo\.cache\whisper` в `E:\whisper-models`
- Установит переменную окружения `WHISPER_CACHE_DIR`
- Предложит удалить старые модели

---

## Ручной способ:

### Шаг 1: Создать директорию на диске E
```powershell
New-Item -ItemType Directory -Path "E:\whisper-models" -Force
```

### Шаг 2: Скопировать модели
```powershell
Copy-Item -Path "$env:USERPROFILE\.cache\whisper\*" -Destination "E:\whisper-models\" -Recurse -Force
```

### Шаг 3: Установить переменную окружения
```powershell
[System.Environment]::SetEnvironmentVariable("WHISPER_CACHE_DIR", "E:\whisper-models", "User")
```

### Шаг 4: Перезапустить PowerShell и сервер
```powershell
# Закройте и откройте PowerShell заново
cd C:\prj\converter\backend
.\run_server.ps1
```

### Шаг 5: (Опционально) Удалить старые модели
```powershell
Remove-Item -Path "$env:USERPROFILE\.cache\whisper" -Recurse -Force
```

---

## Проверка:

После переноса проверьте:

```powershell
# Проверить наличие моделей на диске E
Get-ChildItem "E:\whisper-models" -Recurse | Select-Object Name, Length

# Проверить переменную окружения
$env:WHISPER_CACHE_DIR
```

---

## Важно:

1. **Перезапустите PowerShell** после установки переменной окружения
2. **Перезапустите backend сервер** после переноса
3. Старые модели можно удалить только после проверки, что новые работают

---

## Если что-то пошло не так:

Модели остались на диске C? Проверьте:
- Есть ли права на запись на диск E
- Достаточно ли места на диске E
- Правильно ли указан путь

Можно вернуть обратно:
```powershell
Copy-Item -Path "E:\whisper-models\*" -Destination "$env:USERPROFILE\.cache\whisper\" -Recurse -Force
```



