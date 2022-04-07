import os
import time
import logging
from http import HTTPStatus

from dotenv import load_dotenv
import requests
import telegram

from exceptions import (
    TelegramIsUnavailable,
    PraktikumIsUnavailable,
    AnswerIsEmpty
)

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

PRACTICUM_TOKEN = os.getenv('praktikum_token')
TELEGRAM_TOKEN = os.getenv('tg_token')
TELEGRAM_CHAT_ID = os.getenv('chat_id')

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
    if message == '':
        message = 'Список работ пуст'
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info('Сообщение отправлено')
    except telegram.TelegramError:
        logging.error('Сообщение не отправлено')
        raise TelegramIsUnavailable('Телеграм недоступен')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    answer = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if answer.status_code == HTTPStatus.OK:
        logging.info('Получен ответ от API')
        return answer.json()
    logging.error('Ответ от API не получен')
    raise PraktikumIsUnavailable('Ответ от API не получен')


def check_response(response):
    """Проверка ответа от API."""
    if len(response['homeworks']) == 0:
        logging.info('Список домашних работ пуст')
    elif ('homeworks' not in response) or ('current_date' not in response):
        logging.error('Ответ API пустой')
        raise AnswerIsEmpty('Ответ API пустой')
    elif not isinstance(response['homeworks'], list):
        logging.error('homeworks не список')
        raise ValueError('homeworks не список')
    elif not isinstance(response, dict):
        logging.error('response не словарь')
        raise ValueError('response не словарь')
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
                current_timestamp = response.get('current_date')
                if last_response != response:
                    send_message(bot, response)
                    last_response = response
                else:
                    logging.debug('Статус домашки не изменился')
            else:
                logging.critical('Отсутствуют переменные окружения!')
                raise SystemExit()

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if error_message != message:
                send_message(bot, message)
                error_message = message

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
