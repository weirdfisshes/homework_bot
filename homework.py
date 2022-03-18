import os

import requests

import telegram

import time

import logging

from dotenv import load_dotenv

load_dotenv()

secret_id = os.getenv('chat_id')
secret_praktikum = os.getenv('praktikum_token')
secert_tg = os.getenv('tg_token')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

PRACTICUM_TOKEN = secret_praktikum
TELEGRAM_TOKEN = secert_tg
TELEGRAM_CHAT_ID = secret_id

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Сообщение не отправлено: {error}')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if answer.status_code == 200:
        logging.info('Получен ответ от API')
        return answer.json()
    else:
        logging.error('Ответ от API не получен')
        raise AssertionError('status_code !== 200')


def check_response(response):
    """Проверка ответа от API."""
    if len(response['homeworks']) == 0:
        logging.error('homeworks пустой')
        raise ValueError('homeworks пустой')
    elif 'homeworks' not in response:
        logging.error('В ответе API отсутсвует ключ homeworks')
        raise ValueError('В ответе API отсутсвует ключ homeworks')
    elif 'current_date' not in response:
        logging.error('В ответе API отсутсвует ключ current_date')
        raise ValueError('В ответе API отсутсвует ключ current_date')
    elif type(response['homeworks']) is not list:
        logging.error('homeworks не список')
        raise ValueError('homeworks не список')
    else:
        return response.get('homeworks')


def parse_status(homework):
    """Получение статуса домашней работы."""
    homework_name = homework.get('homework_name')
    try:
        homework_status = homework.get('status')
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        logging.error('Недокументированный статус работы')
        raise KeyError('Недокументированный статус работы')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    last_response = None
    error_message = None
    while True:
        try:
            if check_tokens():
                response = get_api_answer(current_timestamp)
                response = check_response(response)
                response = parse_status(response[0])
                current_timestamp = int(time.time())
                if last_response != response:
                    send_message(bot, response)
                    last_response = response
                else:
                    logging.debug('Статус домашки не изменился')
                time.sleep(RETRY_TIME)
            else:
                logging.critical('Отсутствуют переменные окружения!')
                raise SystemExit()

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if error_message != message:
                send_message(bot, message)
                error_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
