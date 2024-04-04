__all__ = ['InvalidCSVException', 'InvalidCSVHeaderException',
           'InvalidCSVArgumentException']


class BaseImporterException(Exception):
    pass


class InvalidCSVException(BaseImporterException):
    def __init__(self, message, errors=None):
        _message = message
        if errors:
            _message += " Errors: {0}".format(errors)
        super(InvalidCSVException, self).__init__(_message)
        self.errors = errors


class InvalidCSVHeaderException(InvalidCSVException):
    pass


class InvalidCSVArgumentException(InvalidCSVException):
    pass