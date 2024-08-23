__all__ = ['InvalidCSVException', 'InvalidCSVHeaderException',
           'InvalidCSVColumnDefinition', 'CSVTransformException']


class BaseCSVException(Exception):
    pass


class InvalidCSVException(BaseCSVException):
    def __init__(self, message, errors=None):
        _message = message
        if errors:
            _message += " Errors: {0}".format(errors)
        super(InvalidCSVException, self).__init__(_message)
        self.errors = errors


class InvalidCSVHeaderException(InvalidCSVException):
    pass


class InvalidCSVColumnDefinition(InvalidCSVException):
    pass


class CSVTransformException(BaseCSVException):
    def __init__(self, message, original_exception=None):
        super(CSVTransformException, self).__init__(message)
        self.original_exception = original_exception
