FROM node:18-alpine

WORKDIR /app

# Копирование package файлов
COPY package*.json ./

# Установка зависимостей
RUN npm install

# Копирование остальных файлов
COPY . .

# Открытие порта
EXPOSE 5173

# Запуск dev сервера
CMD ["npm", "run", "dev", "--", "--host"]



