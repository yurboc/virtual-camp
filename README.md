# Программный комплекс Virtual Camp

Содержимое репозитория:

* Исходый код Telegram-бота VirtualCampBot <https://t.me/VirtualCampBot>
* Система уведомлений о событиях от обработчиков
* Обработчики:
  * Генератор таблиц для сайта ФСТ-ОТМ
  * Генератор обложек для канала YouTube [в планах]
  * Приёмник сообщений со спутникового телефона [в планах]
  * Туристическая игра "Гусятник" или "Тайный Санта" [в планах]

Используемые технологии:

* python + asyncio
* google-api-python-client
* aiogram
* SQLAlchemy + PostgreSQL
* RabbitMQ + pika
* PyYAML
* Redis

## Установка

Устновка и запуск сервисов, проверено на Debian:

    cd examples/systemd
    sudo cp virtualcamp-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable virtualcamp-*.service
    sudo systemctl start virtualcamp-*.service
    sudo service virtualcamp-bot status
    sudo service virtualcamp-notifier status
    sudo service virtualcamp-worker status

## Удаление

Удаление сервисов, проверено на Debian:

    sudo systemctl stop virtualcamp-*.service
    sudo systemctl disable virtualcamp-worker.service
    sudo systemctl disable virtualcamp-notifier.service
    sudo systemctl disable virtualcamp-bot.service
    sudo rm /etc/systemd/system/virtualcamp-*.service
    sudo systemctl daemon-reload

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
