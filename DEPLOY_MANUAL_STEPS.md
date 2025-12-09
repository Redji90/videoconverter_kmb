# Ручное развертывание на Hugging Face Spaces

Если скрипты не работают, выполните эти команды вручную:

## Шаг 1: Перейдите в директорию Space репозитория

```powershell
cd ..\videoconverter
```

## Шаг 2: Скопируйте файлы из проекта

```powershell
# Из директории C:\prj\converter выполните:
Copy-Item Dockerfile ..\videoconverter\ -Force
Copy-Item .dockerignore ..\videoconverter\ -Force
Copy-Item README_HF_SPACES.md ..\videoconverter\README.md -Force
Copy-Item backend ..\videoconverter\ -Recurse -Force
Copy-Item frontend ..\videoconverter\ -Recurse -Force
```

## Шаг 3: Очистите ненужные файлы

```powershell
cd ..\videoconverter

# Удалите node_modules и dist из frontend
if (Test-Path "frontend\node_modules") {
    Remove-Item frontend\node_modules -Recurse -Force
}
if (Test-Path "frontend\dist") {
    Remove-Item frontend\dist -Recurse -Force
}

# Удалите __pycache__ из backend
Get-ChildItem backend -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem backend -Recurse -File -Filter "*.pyc" | Remove-Item -Force
```

## Шаг 4: Отправьте изменения в Git

```powershell
git add .
git commit -m "Add Video to Text Converter application"
git push
```

## Альтернатива: Используйте Git Bash или обычный CMD

Если PowerShell вызывает проблемы, используйте Git Bash:

```bash
cd ../videoconverter
cp ../converter/Dockerfile .
cp ../converter/.dockerignore .
cp ../converter/README_HF_SPACES.md README.md
cp -r ../converter/backend .
cp -r ../converter/frontend .

# Очистка
rm -rf frontend/node_modules frontend/dist
find backend -type d -name "__pycache__" -exec rm -rf {} +
find backend -name "*.pyc" -delete

# Git
git add .
git commit -m "Add Video to Text Converter application"
git push
```

