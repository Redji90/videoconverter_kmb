# Настройка для PowerShell (Windows)

## Проблема с активацией виртуального окружения

В PowerShell команда `venv\Scripts\activate` не работает. Нужно использовать другой синтаксис.

## Решение

### Вариант 1: Использовать полный путь с расширением
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Вариант 2: Если получаете ошибку политики выполнения

PowerShell может блокировать выполнение скриптов. Выполните:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Затем попробуйте снова:
```powershell
.\venv\Scripts\Activate.ps1
```

### Вариант 3: Использовать CMD вместо PowerShell

Откройте обычную командную строку (CMD) и используйте:
```cmd
cd backend
python -m venv venv
venv\Scripts\activate
```

## Полная последовательность команд для PowerShell

```powershell
# 1. Перейти в директорию backend
cd C:\prj\converter\backend

# 2. Создать виртуальное окружение (если еще не создано)
python -m venv venv

# 3. Разрешить выполнение скриптов (только первый раз)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 4. Активировать виртуальное окружение
.\venv\Scripts\Activate.ps1

# 5. Установить зависимости
pip install -r requirements.txt

# 6. Запустить сервер
uvicorn app.main:app --reload
```

## Проверка активации

После активации вы должны увидеть `(venv)` в начале строки:
```
(venv) PS C:\prj\converter\backend>
```

## Альтернатива: Использовать готовые скрипты

В директории `backend` созданы скрипты для упрощения работы:

### 1. Создание виртуального окружения:
```powershell
cd C:\prj\converter\backend
.\create_venv.ps1
```

### 2. Установка зависимостей:
```powershell
.\install_deps.ps1
```

### 3. Запуск сервера:
```powershell
.\run_server.ps1
```

## Альтернатива: Использовать активацию через Python

Если проблемы продолжаются, можно запускать команды напрямую через Python из venv:

```powershell
cd C:\prj\converter\backend
# Создать venv (если еще не создан)
python -m venv venv
# или
py -m venv venv

# Установить зависимости
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Запустить сервер
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Или создать alias:
```powershell
# В PowerShell профиле
function Activate-Venv {
    & ".\venv\Scripts\Activate.ps1"
}
```

## Полезные команды

```powershell
# Проверить версию Python
python --version

# Проверить установленные пакеты
pip list

# Деактивировать виртуальное окружение
deactivate

# Удалить виртуальное окружение (если нужно пересоздать)
Remove-Item -Recurse -Force venv
```

