# Быстрое решение проблемы аутентификации Git

## Проблема
```
git: 'credential-manager-core' is not a git command
remote: Password authentication in git is no longer supported
```

## Решение (3 простых шага)

### Шаг 1: Исправьте credential helper

```powershell
git config --global credential.helper wincred
git config --global --unset credential.helper manager-core
```

### Шаг 2: Создайте токен доступа на Hugging Face

1. Откройте: https://huggingface.co/settings/tokens
2. Нажмите **"New token"**
3. Имя: `videoconverter-space`
4. Роль: **"Write"** (важно!)
5. Нажмите **"Generate token"**
6. **Скопируйте токен** (показывается только один раз!)

### Шаг 3: Выполните push с токеном

```powershell
git push
```

Когда Git запросит:
- **Username:** `Vladislava11`
- **Password:** вставьте ваш токен (не пароль!)

Git сохранит токен в Windows Credential Manager, и в следующий раз не будет запрашивать.

## Альтернатива: Использование SSH

Если токены не подходят, используйте SSH:

```powershell
# 1. Измените URL на SSH
git remote set-url origin git@hf.co:spaces/Vladislava11/videoconverter

# 2. Убедитесь, что у вас есть SSH ключ на Hugging Face
# Добавьте ключ здесь: https://huggingface.co/settings/keys

# 3. Выполните push
git push
```

## Проверка настройки

```powershell
# Проверьте текущий remote URL
git remote -v

# Проверьте credential helper
git config --global credential.helper
```

