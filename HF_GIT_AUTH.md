# Настройка аутентификации Git для Hugging Face Spaces

## Проблема
Git требует токен доступа для работы с Hugging Face Spaces, а не обычный пароль.

## Решение 1: Использование токена доступа (рекомендуется)

### Шаг 1: Создайте токен доступа

1. Откройте https://huggingface.co/settings/tokens
2. Нажмите "New token"
3. Дайте токену имя (например, "videoconverter-space")
4. Выберите роль "Write" (для возможности push)
5. Нажмите "Generate token"
6. **Скопируйте токен** (он показывается только один раз!)

### Шаг 2: Используйте токен при push

Когда Git запросит пароль, используйте токен вместо пароля:

```powershell
git push
# Username: Vladislava11
# Password: [вставьте ваш токен здесь]
```

### Шаг 3: Сохраните токен (опционально)

Чтобы не вводить токен каждый раз, можно настроить Git credential helper:

**Windows (Git Credential Manager):**
```powershell
git config --global credential.helper manager-core
```

**Или использовать встроенный Windows Credential Manager:**
```powershell
git config --global credential.helper wincred
```

После этого Git будет запрашивать токен один раз и сохранит его.

## Решение 2: Использование SSH (альтернатива)

### Шаг 1: Проверьте наличие SSH ключа

```powershell
ls ~/.ssh/id_rsa.pub
```

Если файла нет, создайте SSH ключ:
```powershell
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

### Шаг 2: Добавьте SSH ключ на Hugging Face

1. Скопируйте содержимое публичного ключа:
```powershell
cat ~/.ssh/id_rsa.pub
```

2. Откройте https://huggingface.co/settings/keys
3. Нажмите "Add new key"
4. Вставьте публичный ключ
5. Сохраните

### Шаг 3: Измените URL репозитория на SSH

```powershell
git remote set-url origin git@hf.co:spaces/Vladislava11/videoconverter
git push
```

## Решение 3: Встроить токен в URL (не рекомендуется для безопасности)

```powershell
git remote set-url origin https://Vladislava11:YOUR_TOKEN@huggingface.co/spaces/Vladislava11/videoconverter
git push
```

⚠️ **Внимание:** Этот метод небезопасен, так как токен будет виден в истории Git.

## Рекомендуемый подход

Используйте **Решение 1** с Git Credential Manager - это самый безопасный и удобный способ.

