# ⚡ Быстрое развертывание на Hugging Face Spaces

## 🚀 Автоматическое развертывание

### Windows (PowerShell)

```powershell
# 1. Клонируйте Space репозиторий
git clone https://huggingface.co/spaces/Vladislava11/videoconverter ../videoconverter

# 2. Запустите скрипт развертывания
.\deploy_to_spaces.ps1 ../videoconverter

# 3. Перейдите в директорию Space и отправьте изменения
cd ../videoconverter
git add .
git commit -m "Add Video to Text Converter application"
git push
```

### Linux/Mac (Bash)

```bash
# 1. Клонируйте Space репозиторий
git clone https://huggingface.co/spaces/Vladislava11/videoconverter ../videoconverter

# 2. Сделайте скрипт исполняемым и запустите
chmod +x deploy_to_spaces.sh
./deploy_to_spaces.sh ../videoconverter

# 3. Перейдите в директорию Space и отправьте изменения
cd ../videoconverter
git add .
git commit -m "Add Video to Text Converter application"
git push
```

## 📋 Ручное развертывание

Если скрипты не работают, выполните вручную:

```bash
# 1. Клонируйте Space репозиторий
git clone https://huggingface.co/spaces/Vladislava11/videoconverter
cd videoconverter

# 2. Скопируйте файлы из проекта
cp ../converter/Dockerfile .
cp ../converter/.dockerignore .
cp ../converter/README_HF_SPACES.md README.md
cp -r ../converter/backend .
cp -r ../converter/frontend .

# 3. Удалите ненужные файлы
rm -rf frontend/node_modules frontend/dist
find backend -type d -name "__pycache__" -exec rm -rf {} +
find backend -name "*.pyc" -delete

# 4. Отправьте изменения
git add .
git commit -m "Add Video to Text Converter application"
git push
```

## ⏱️ Время развертывания

- **Первая сборка**: 10-15 минут (установка зависимостей, сборка frontend)
- **Последующие обновления**: 5-10 минут

## ✅ Проверка

После `git push`:
1. Откройте [ваш Space](https://huggingface.co/spaces/Vladislava11/videoconverter)
2. Проверьте вкладку "Logs" для просмотра процесса сборки
3. После успешной сборки приложение будет доступно

## 🐛 Решение проблем

### Ошибка "Permission denied" (Linux/Mac)
```bash
chmod +x deploy_to_spaces.sh
```

### Ошибка выполнения скрипта (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Файлы не найдены
Убедитесь, что вы находитесь в корневой директории проекта `converter/`

## 📚 Подробная документация

См. [DEPLOY_TO_HF_SPACES.md](DEPLOY_TO_HF_SPACES.md) для подробных инструкций.

