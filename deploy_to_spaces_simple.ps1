param(
    [string]$SpaceRepo = "../videoconverter"
)

if (-not (Test-Path $SpaceRepo)) {
    Write-Host "Ошибка: Директория не найдена: $SpaceRepo" -ForegroundColor Red
    Write-Host "Использование: .\deploy_to_spaces_simple.ps1 [путь]"
    exit 1
}

Write-Host "Копирование файлов в $SpaceRepo..." -ForegroundColor Green

Copy-Item -Path "Dockerfile" -Destination "$SpaceRepo\" -Force
Copy-Item -Path ".dockerignore" -Destination "$SpaceRepo\" -Force
Copy-Item -Path "README_HF_SPACES.md" -Destination "$SpaceRepo\README.md" -Force
Copy-Item -Path "backend" -Destination "$SpaceRepo\" -Recurse -Force
Copy-Item -Path "frontend" -Destination "$SpaceRepo\" -Recurse -Force

Write-Host "Очистка ненужных файлов..." -ForegroundColor Yellow

if (Test-Path "$SpaceRepo\frontend\node_modules") {
    Remove-Item -Path "$SpaceRepo\frontend\node_modules" -Recurse -Force
}

if (Test-Path "$SpaceRepo\frontend\dist") {
    Remove-Item -Path "$SpaceRepo\frontend\dist" -Recurse -Force
}

Get-ChildItem -Path "$SpaceRepo\backend" -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path "$SpaceRepo\backend" -Recurse -File -Filter "*.pyc" | Remove-Item -Force

Write-Host "Готово!" -ForegroundColor Green
Write-Host ""
Write-Host "Следующие шаги:"
Write-Host "  cd $SpaceRepo"
Write-Host "  git add ."
Write-Host "  git commit -m 'Add Video to Text Converter application'"
Write-Host "  git push"

