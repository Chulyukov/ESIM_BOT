# Используем базовый образ Ubuntu 24.04
FROM ubuntu:24.04

# Устанавливаем необходимые зависимости
RUN apt update && apt install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    curl \
    cron \
    nodejs \
    npm \
    debconf-utils

# Установка MySQL с указанием пароля root
RUN echo "mysql-server mysql-server/root_password password kexibq528123" | debconf-set-selections && \
    echo "mysql-server mysql-server/root_password_again password kexibq528123" | debconf-set-selections && \
    apt install -y mysql-server

# Устанавливаем pm2
RUN npm install pm2 -g

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в рабочую директорию контейнера
COPY requirements.txt .

# Создаем виртуальное окружение с Python 3.12 и активируем его
RUN python3.12 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Устанавливаем зависимости Python из requirements.txt в виртуальной среде
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы и папки из текущей директории в рабочую директорию контейнера
COPY . .

# Добавляем задачи cron
RUN echo "10 * * * * /app/venv/bin/python /app/scripts/check_remaining_traffic.py >> /var/log/cron.log 2>&1" > /etc/cron.d/check_remaining_traffic \
    && echo "* * * * * /app/venv/bin/python /app/scripts/update_bnesim_products.py >> /var/log/cron.log 2>&1" >> /etc/cron.d/check_remaining_traffic \
    && chmod 0644 /etc/cron.d/check_remaining_traffic

# Устанавливаем права для файлов скриптов
RUN chmod +x /app/scripts/check_remaining_traffic.py /app/scripts/update_bnesim_products.py

# Запускаем cron и pm2
CMD cron && pm2-runtime start main.py --name esim_bot --interpreter /app/venv/bin/python