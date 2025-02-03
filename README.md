# Программный комплекс Virtual Camp

[![Black Lint badge](https://github.com/yurboc/virtual-camp/actions/workflows/black.yml/badge.svg?branch=main)](https://github.com/yurboc/virtual-camp/actions/workflows/black.yml)
[![flake8 Lint badge](https://github.com/yurboc/virtual-camp/actions/workflows/flake8.yml/badge.svg?branch=main)](https://github.com/yurboc/virtual-camp/actions/workflows/flake8.yml)

Содержимое репозитория:

* Исходый код Telegram-бота VirtualCampBot <https://t.me/VirtualCampBot>
* Система уведомлений о событиях от обработчиков
* Обработчики:
  * Генератор таблиц для сайта ФСТ-ОТМ
  * Генератор обложек для канала YouTube
* Модули:
  * Диагностика (расшифровка полученных сообщений в JSON)
  * Регистрация (ввод телефона и имени пользователя)
  * Отслеживание посещений по абонементу (например, скалодром)

Используемые технологии:

* python + asyncio
* google-api-python-client
* aiogram
* SQLAlchemy + PostgreSQL
* RabbitMQ + pika
* PyYAML
* Redis

## Установка

### Подготовка сервера

Проверено на сервере от RuVDS

    #
    # Begin from 'root' user
    #
    adduser yurboc
    adduser yurboc sudo

    #
    # Login from 'yurboc' user
    #

    # Install packages
    sudo apt update
    sudo apt dist-upgrade
    sudo apt install python3 python-is-python3 python3-venv libaugeas0
    sudo apt install vim git nginx postgresql redis rabbitmq-server

    # Set SSH access by key
    ssh-keygen -t rsa
    cat ~/.ssh/id_rsa.pub
    vim .ssh/authorized_keys # add public key

    # Get source code
    cd /home/yurboc
    mkdir projects
    git clone git@github.com:yurboc/virtual-camp.git

    # Set timezone
    sudo timedatectl set-timezone Europe/Moscow

    # Prepare DB
    sudo -i -u postgres
    createuser --interactive # create user 'virtualcamp'
    createdb virtualcamp_db
    sudo vim /etc/postgresql/16/main/postgresql.conf # timezone -> Europe/Moscow
    psql virtualcamp_db -c 'SELECT pg_reload_conf()'
    psql virtualcamp_db
    # ALTER USER virtualcamp WITH PASSWORD 'your-password-here';
    # ALTER DATABASE virtualcamp_db OWNER TO virtualcamp;
    # exit

    # Create certificate
    sudo python3 -m venv /opt/certbot/
    sudo /opt/certbot/bin/pip install --upgrade pip
    sudo /opt/certbot/bin/pip install certbot certbot-nginx
    sudo ln -s /opt/certbot/bin/certbot /usr/bin/certbot
    sudo certbot --nginx
    echo "0 0,12 * * * root /opt/certbot/bin/python -c 'import random; import time; time.sleep(random.random() * 3600)' && sudo certbot renew -q" | sudo tee -a /etc/crontab > /dev/null
    sudo /opt/certbot/bin/pip install --upgrade certbot certbot-nginx

    # Configure Nginx as reverse proxy
    cd /etc/nginx/sites-available/
    sudo mv default default-old
    sudo cp ~/projects/virtual-camp/examples/nginx/default ./
    sudo cp ~/projects/virtual-camp/examples/nginx/telegram-webhook ./
    cd /etc/nginx/sites-enabled
    sudo ln -s /etc/nginx/sites-available/telegram-webhook
    sudo vim default # replace server info
    sudo vim telegram-webhook # replace server info
    sudo service nginx restart

    # Enable RabbitMQ management (for /info command)
    sudo rabbitmq-plugins enable rabbitmq_management

    # Create virtual environment
    cd /home/yurboc/projects/virtual-camp
    python -m venv venv
    source venv/bin/activate

    # Install required Python modules
    python -m pip install --upgrade pip
    pip install -r requirements.txt

    #
    # Create file src/config/config.yaml from config.default.yaml
    #

    #
    # Create and run services (next chapter)
    #

    # Start bot, worker and notifier in interactive mode
    cd /home/yurboc/projects/virtual-camp/src
    python -u notifier_main.py
    python -u worker_main.py
    python -u bot_main.py

### Настройка окружения

Файл *src/config/config.yaml* создаётся на основе *src/config/config.default.yaml*

Файл *config.yaml* не добавляется в репозиторий, т.к. содежит логины и пароли.

### Устновка и запуск сервисов

Проверено на Debian

    cd /home/yurboc/projects/virtual-camp/examples/systemd
    sudo cp virtualcamp-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable virtualcamp-*.service
    sudo systemctl start virtualcamp-*.service
    sudo service virtualcamp-bot status
    sudo service virtualcamp-notifier status
    sudo service virtualcamp-worker status

### Обновление и перезапуск сервисов

Проверено на Debian

    cd /home/yurboc/projects/virtual-camp
    ./sync.sh # requires user password

## Удаление

Удаление сервисов, проверено на Debian:

    sudo systemctl stop virtualcamp-*.service
    sudo systemctl disable virtualcamp-worker.service
    sudo systemctl disable virtualcamp-notifier.service
    sudo systemctl disable virtualcamp-bot.service
    sudo rm /etc/systemd/system/virtualcamp-*.service
    sudo systemctl daemon-reload

Удаление исходного кода:

    cd /home/yurboc/projects
    rm -rf virtual-camp

Далее можно удалить все модули, установленные через apt install

## Тестирование

Автономная проверка работоспособности компонентов комплекса:

### Очереди сообщений

Проверка очередей:

    sudo rabbitmq-plugins enable rabbitmq_management
    sudo rabbitmqctl status
    sudo rabbitmqctl list_queues

Удаление очередей:

    rabbitmqadmin delete queue name='tasks_queue'
    rabbitmqadmin delete queue name='results_queue'

### fst-otm-tables

Назначение: генерация таблиц для сайта ФСТ-ОТМ.

Используемые очереди: "tasks_queue", "results_queue"

Тип задания "job_type" = "table_generator"

Допустимые значения для поля "job":

* "all"
* "sportsmeny"
* "razrjad_docs"
* "sportivnye_sudi"
* "trips"

Отправка заданий и получение результатов вручную:

    rabbitmqadmin publish routing_key='tasks_queue' payload='{"job_type": "table_generator", "job": "all"}'
    rabbitmqadmin get queue='results_queue' ackmode=ack_requeue_true count=100
