###  homework_bot
### Описание
Telegram-бот для оповещения об изменении статуса проверки (review) домашней работы Яндекс.Практикум.
Раз в 10 минут бот делает запрос к API и в случае изменения статуса, либо возникновении неполадок отправляет соответствующее письмо в Telegram.
Для корректной работы бота необходимы токены Практикума и Telegram, а также ID чата в Telegram, куда будут отправляться сообщения. У API Практикум.

### Стек
- python
- dotenv
- telegram-bot
- pytest
- requests

### Запуск проекта в dev-режиме
Инструкция ориентирована на операционную систему windows и утилиту git bash.
Для прочих инструментов используйте аналоги команд для вашего окружения.

1. Клонируйте репозиторий и перейдите в него в командной строке:
git clone https://github.com/Banes31/homework_bot.git
cd homework_bot
2. Установите и активируйте виртуальное окружение
python -m venv venv
source venv/Scripts/activate
3. Установите зависимости из файла requirements.txt
pip install -r requirements.txt
4. В консоле импортируйте токены для Яндекс.Практикум и Телеграмм:
export PRACTICUM_TOKEN=<PRACTICUM_TOKEN>
export TELEGRAM_TOKEN=<TELEGRAM_TOKEN>
export CHAT_ID=<CHAT_ID>
5. Запустите бота, выполнив команду:
python homework.py
6. Деактивируйте виртуальное окружение (после работы), выполнив команду:
deactivate

### Автор
[Шадрин Ян](https://github.com/Iankel86)
