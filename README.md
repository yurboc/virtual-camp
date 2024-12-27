# virtual-camp

Содержимое репозитория:

* Исходый код Telegram-бота VirtualCampBot <https://t.me/VirtualCampBot>
* Обработчики таблиц для ФСТ-ОТМ
* Система уведомлений о событиях

Используемые технологии:

* python + asyncio
* google-api-python-client
* aiogram
* SQLAlchemy + PostgreSQL
* RabbitMQ + pika
* PyYAML
* Redis

# install

Устновка и запуск сервисов, проверено на Debian:

    cd examples/systemd
    sudo cp virtualcamp-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable virtualcamp-*.service
    sudo systemctl start virtualcamp-*.service
    sudo service virtualcamp-bot status
    sudo service virtualcamp-notifier status
    sudo service virtualcamp-tables status

# uninstall

Удаление сервисов, проверено на Debian:

    sudo systemctl stop virtualcamp-*.service
    sudo systemctl disable virtualcamp-tables.service
    sudo systemctl disable virtualcamp-notifier.service
    sudo systemctl disable virtualcamp-bot.service
    sudo rm /etc/systemd/system/virtualcamp-*.service
    sudo systemctl daemon-reload

# test

Автономная проверка работоспособности:

## fst-otm-tables

Допустимые значения для поля "job":

* "all"
* "sportsmeny"
* "razrjad_docs"
* "sportivnye_sudi"
* "trips"

Проверка очередей:

    sudo rabbitmq-plugins enable rabbitmq_management
    sudo rabbitmqctl status
    sudo rabbitmqctl list_queues

Отправка заданий и получение результатов вручную:

    rabbitmqadmin publish routing_key='tasks_queue' payload='{"job": "all"}'
    rabbitmqadmin get queue='results_queue' ackmode=ack_requeue_true count=100

Удаление очередей:

    rabbitmqadmin delete queue name='tasks_queue'
    rabbitmqadmin delete queue name='results_queue'
