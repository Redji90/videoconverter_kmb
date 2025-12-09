# Скрипт PowerShell для развертывания проекта на Hugging Face Spaces
# Использование: .\deploy_to_spaces.ps1 [путь_к_space_репозиторию]

param(
    [string]$SpaceRepo = "../videoconverter"
)

if (-not (Test-Path $SpaceRepo)) {
    Write-Host "Ошибка: Директория Space репозитория не найдена: $SpaceRepo" -ForegroundColor Red
    Write-Host "Использование: .\deploy_to_spaces.ps1 [путь_к_space_репозиторию]"
    Write-Host ""
    Write-Host "Пример:"
    Write-Host "  git clone https://huggingface.co/spaces/Vladislava11/videoconverter ../videoconverter"
    Write-Host "  .\deploy_to_spaces.ps1 ../videoconverter"
    exit 1
}

Write-Host "Начало развертывания на Hugging Face Spaces..." -ForegroundColor Green
Write-Host "Целевая директория: $SpaceRepo"

# Копирование файлов
Write-Host "Копирование файлов..." -ForegroundColor Yellow

# Основные файлы
Copy-Item -Path "Dockerfile" -Destination "$SpaceRepo\" -Force
Copy-Item -Path ".dockerignore" -Destination "$SpaceRepo\" -Force
Copy-Item -Path "README_HF_SPACES.md" -Destination "$SpaceRepo\README.md" -Force

# Backend
Write-Host "  Копирование backend..." -ForegroundColor Cyan
Copy-Item -Path "backend" -Destination "$SpaceRepo\" -Recurse -Force

# Frontend
Write-Host "  Копирование frontend..." -ForegroundColor Cyan
Copy-Item -Path "frontend" -Destination "$SpaceRepo\" -Recurse -Force

# Удаление ненужных файлов из frontend
Write-Host "  Очистка frontend..." -ForegroundColor Yellow
if (Test-Path "$SpaceRepo\frontend\node_modules") {
    Remove-Item -Path "$SpaceRepo\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "$SpaceRepo\frontend\dist") {
    Remove-Item -Path "$SpaceRepo\frontend\dist" -Recurse -Force -ErrorAction SilentlyContinue
}

# Удаление ненужных файлов из backend
Write-Host "  Очистка backend..." -ForegroundColor Yellow
Get-ChildItem -Path "$SpaceRepo\backend" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path "$SpaceRepo\backend" -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Файлы скопированы!" -ForegroundColor Green
Write-Host ""
Write-Host "Следующие шаги:" -ForegroundColor Yellow
Write-Host "  1. cd $SpaceRepo"
Write-Host "  2. git add ."
Write-Host "  3. git commit -m 'Add Video to Text Converter application'"
Write-Host "  4. git push"
Write-Host ""
Write-Host "После push приложение будет доступно на:" -ForegroundColor Cyan
$url = "https://huggingface.co/spaces/Vladislava11/videoconverter"
Write-Host "  $url"
