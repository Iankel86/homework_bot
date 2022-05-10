import logging
import json
import os
import time
import requests
import telegram
import settings
# from .settings import RETRY_TIME

from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# PRACTICUM_TOKEN = 'AQAAAABbscPSAAYckRyyz4hf00aei3_VpBYOGJE'
# TELEGRAM_TOKEN = '5299797872:AAHECGc7Ihyw_6k-7isDZOBM4H_O_cvjQ20'
# TELEGRAM_CHAT_ID = '329734189'

# RETRY_TIME = settings.RETRY_TIME
# RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


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
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise requests.HTTPError(response)
        return response.json()
    except requests.exceptions.RequestException as error:
        raise Exception(f'Ошибка при запросе к эндпойнту: {error}')
    except json.decoder.JSONDecodeError as error:
        raise Exception((f'Ответ {response.text} получен не в виде JSON: '
                         f'{error}'))


def check_response(response):
    """Проверяем данные в response."""
    if not isinstance(response, dict):
        raise TypeError('Ответ получен не в виде словаря')
    key = 'homeworks'
    if key not in response:
        raise KeyError(f'В response нет ключа {key}')
    if not isinstance(response[key], list):
        raise TypeError('Домашняя работа получена не в виде списка')
    return response[key]


def parse_status(homework):
    """Информация о статусе работы ."""
    if not isinstance(homework, dict):
        raise TypeError('Формат ответа API отличается от ожидаемого')
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
    except KeyError as error:
        raise KeyError(f'В словаре домашней работы нет ключа {error}')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(('Недокументированный статус домашней '
                        f'работы: {homework_status}'))
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка наличия токенов."""
    if PRACTICUM_TOKEN is None:
        logging.error('Переменная PRACTICUM_TOKEN не задана.')
        return False
    if TELEGRAM_TOKEN is None:
        logging.error('Переменная TELEGRAM_TOKEN не задана.')
        return False
    if TELEGRAM_CHAT_ID is None:
        logging.error('Переменная TELEGRAM_CHAT_ID не задана.')
        return False
    else:
        logging.info('Проверка переменных прошла успешна.')
        return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутствуют обязательные переменные окружения!')
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
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
