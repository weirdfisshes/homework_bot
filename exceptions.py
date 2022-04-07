class PraktikumIsUnavailable(Exception):
    """Ответ от сервера не получен."""

    pass


class TelegramIsUnavailable(Exception):
    """Ответ от сервера не получен."""

    pass


class AnswerIsEmpty(Exception):
    """Ответ от сервера пустой."""

    pass
