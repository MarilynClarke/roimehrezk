__all__ = ['InvalidCSVException', 'InvalidCSVHeaderException',
           'InvalidCSVArgumentException']


class BaseImporterException(Exception):
    pass


class InvalidCSVException(BaseImporterException):
    def __init__(self, message, errors=None):
        super(InvalidCSVException, self).__init__(message)
        self.errors = errors


class InvalidCSVHeaderException(InvalidCSVException):
    pass


class InvalidCSVArgumentException(InvalidCSVException):
    pass