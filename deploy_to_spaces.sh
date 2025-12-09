#!/bin/bash

# Скрипт для развертывания проекта на Hugging Face Spaces
# Использование: ./deploy_to_spaces.sh [путь_к_space_репозиторию]

SPACE_REPO="${1:-../videoconverter}"

if [ ! -d "$SPACE_REPO" ]; then
    echo "❌ Директория Space репозитория не найдена: $SPACE_REPO"
    echo "Использование: ./deploy_to_spaces.sh [путь_к_space_репозиторию]"
    echo ""
    echo "Пример:"
    echo "  git clone https://huggingface.co/spaces/Vladislava11/videoconverter ../videoconverter"
    echo "  ./deploy_to_spaces.sh ../videoconverter"
    exit 1
fi

echo "🚀 Начало развертывания на Hugging Face Spaces..."
echo "📁 Целевая директория: $SPACE_REPO"

# Копирование файлов
echo "📋 Копирование файлов..."

# Основные файлы
cp Dockerfile "$SPACE_REPO/"
cp .dockerignore "$SPACE_REPO/"
cp README_HF_SPACES.md "$SPACE_REPO/README.md"

# Backend
echo "  📦 Копирование backend..."
cp -r backend "$SPACE_REPO/"

# Frontend
echo "  📦 Копирование frontend..."
cp -r frontend "$SPACE_REPO/"

# Удаление ненужных файлов из frontend
echo "  🧹 Очистка frontend..."
rm -rf "$SPACE_REPO/frontend/node_modules" 2>/dev/null || true
rm -rf "$SPACE_REPO/frontend/dist" 2>/dev/null || true

# Удаление ненужных файлов из backend
echo "  🧹 Очистка backend..."
find "$SPACE_REPO/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$SPACE_REPO/backend" -type d -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Файлы скопированы!"
echo ""
echo "📝 Следующие шаги:"
echo "  1. cd $SPACE_REPO"
echo "  2. git add ."
echo "  3. git commit -m 'Add Video to Text Converter application'"
echo "  4. git push"
echo ""
echo "🌐 После push приложение будет доступно на:"
echo "   https://huggingface.co/spaces/Vladislava11/videoconverter"

