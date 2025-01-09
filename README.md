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

### Установка зависимостей

Проверено на Python 3.9.2

    sudo apt install python3
    python -m pip install --upgrade pip
    pip install -r requirements.txt

### Устновка и запуск сервисов

Проверено на Debian

    cd examples/systemd
    sudo cp virtualcamp-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable virtualcamp-*.service
    sudo systemctl start virtualcamp-*.service
    sudo service virtualcamp-bot status
    sudo service virtualcamp-notifier status
    sudo service virtualcamp-worker status

### Настройка окружения

Файл *src/config/config.yaml* создаётся на основе *src/config/config.default.yaml*

Файл *config.yaml* не добавляется в репозиторий, т.к. содежит логины и пароли.

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
