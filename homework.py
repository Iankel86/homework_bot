import logging
import json
import os
import time
import requests
import telegram
import settings

from dotenv import load_dotenv
from http import HTTPStatus
# from settings import ENDPOINT, HEADERS
from constants import ENDPOINT
# from constants import HEADERS
# - перепробывал все возможные варианты, начал еще с 10.05.2022
# даже отдельно создал файл, думал в settings может нельзя,но все равно ошибка:
# Проблема с работой. Ошибка хаха при запросе к эндпойнту: <Response [401]>

load_dotenv()

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


# ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        raise telegram.TelegramError('Ошибка отправки сообщения в телеграм: '
                                     f'{error}')


def get_api_answer(current_timestamp):
    """Функция запроса к API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params=params)
        if response.status_code != HTTPStatus.OK:
            raise requests.HTTPError(response)
        return response.json()
    except requests.exceptions.RequestException as error:
        raise Exception(f'хаха при запросе к эндпойнту: {error}')
    except json.decoder.JSONDecodeError as error:
        raise Exception((f'Ответ {response.text} получен не в виде JSON: '
                         f'{error}'))


def check_response(response):
    """Проверяем данные в response."""
    if not isinstance(response, dict):
        raise TypeError('Ответ получен не в виде словаря')
    if 'homeworks' not in response:
        raise KeyError('В response нет ключа homeworks')
    if not isinstance(response['homeworks'], list):
        raise TypeError('Домашняя работа получена не в виде списка')
    return response['homeworks']


def parse_status(homework):
    """Информация о статусе работы ."""
    if not isinstance(homework, dict):
        raise TypeError('Формат ответа API отличается от ожидаемого')
    if 'homework_name' not in homework:
        raise KeyError('Ошибка с ключем homework_name')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise KeyError('Ошибка с ключем status')
    homework_status = homework['status']
    if homework_status not in settings.HOMEWORK_STATUSES:
        raise KeyError(('Недокументированный статус домашней '
                        f'работы: {homework_status}'))
    verdict = settings.HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Нет обязательных переменных окружения!')
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - 11000500)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.debug('Нет обновлений в статусах работ')
            for homework in homeworks:
                message = parse_status(homework)
                send_message(bot, message)
                logger.info(('Сообщение отправленно в телеграм: '
                            f'{message}'))
            current_timestamp = response.get('current_date', current_timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(f'Проблема с работой. Ошибка {error}')
        finally:
            time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()
