# Инструкция по запуску Backend

## Правильная команда активации для PowerShell:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
```

**Если возникает ошибка "не может загрузить файл", выполните:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Затем установите зависимости (если еще не установлены):

```powershell
pip install -r requirements.txt
```

## Запустите сервер:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер будет доступен на: **http://localhost:8000**

## Проверка работы:

- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Тестовый endpoint: http://localhost:8000/api/test

