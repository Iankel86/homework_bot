import logging
import os
import time
import requests
import telegram


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
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
    except Exception as error:
        logging.error(f'Ошибка при обращении к API Telegram: {error}')


def get_api_answer(current_timestamp):
    """Функция запроса к API Яндекс.Практикум."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    response = homework_statuses.json()
    if homework_statuses.status_code != 200:
        raise Exception(
            f'Статус код не 200!'
            f'Статус код {homework_statuses.status_code}'
        )
    return response


def check_response(response):
    """Проверяем данные в response."""
    homework = response['homeworks']
    if not homework:
        raise Exception('Нет ключа homeworks')
    if type(homework) is not list:
        raise Exception('домашки приходят не в виде списка в ответ от API')
    if response is None:
        raise Exception('Пустой запрос')
    if not isinstance(response, dict):
        logging.error('На входе некорректный тип данных')
    return homework


def parse_status(homework):
    """Информация о статусе работы ."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
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
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    check_tokens()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response(response)
            homework = response['homeworks'][0]
            if homework:
                logging.info(f'{homework} найден. Данные отправлены')
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logging.info(f'{homework} не найден. Словарь отсутствует')
                logging.debug(f'Следующая попытка через {RETRY_TIME} сек')
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Проблема с работой. Ошибка{error}')
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
