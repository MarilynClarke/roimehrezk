import csv

from .exceptions import *


class CSVModelReader(object):

    DEFAULT_ROW_INVALID_MESSAGE = "Row {0} is invalid."

    def __init__(self, csv_file, dialect=None, encoding='utf-8',
                 columns=None, fail_fast=True, max_failures=None,
                 strip_white_spaces=True, header_included=True, skip_lines=0):
        """
        Bare minimal CSV parser class that provides:
            * Validation. You can specify different requirements
              for your columns. See columns format below.
            * The ability to specify a connector that will return a rich object
              instead of a list or dict.
            * By default returns a dict with the names of the columns specified
              so you don't have to deal with indexes anymore.
            * Let you specify which fields are required.
            * A clear API to support your code.

        Params:
          - csv_file: a stream (a file or StringIO) to read from.
          - dialect: The dialect to interpret the CSV file.
          - encoding: Optional. Specify if you're not using UTF-8.
          - columns: The description of your models. The format is below.

        Columns format:

        columns = [
            {'name': 'column'},  # Required by default
            {'name': 'column', 'required': False},
            {'name': 'column', 'choices': ['value1', 'value2']},
            {'name': 'column', 'validator': lambda c: c.startswith('http')},
        ]
        """
        self.reader = csv.reader(csv_file, dialect=dialect)
        self.encoding = encoding
        self.columns = columns
        self.fail_fast = fail_fast
        self.max_failures = max_failures
        self.failure_count = 0
        self.row_counter = 0
        self.strip_white_spaces = strip_white_spaces
        self.header_included = header_included
        self.skip_lines = skip_lines
        self.errors = {}

        self._validate_model_definition(self.columns)

        self.model_fields = [c['name'] for c in self.columns]

        self._skip_lines()

        if header_included:
            self.csv_header = self._read_header()
            self._validate_header()

    def _validate_model_definition(self, columns):
        processed_names = []
        for index, column in enumerate(columns):
            if 'name' not in column:
                raise InvalidCSVColumnDefinition(
                    "The column {0} doesn't have a name.".format(index))

            column_name = column['name']

            if column['name'] in processed_names:
                raise InvalidCSVColumnDefinition(
                    "Column name {0} is repeated".format(column_name))

            processed_names.append(column_name)

            if 'validator' in column:
                if not hasattr(column['validator'], '__call__'):
                    raise InvalidCSVColumnDefinition(
                        "The validator for the column {0} "
                        "is not callable.".format(column_name))

            if 'default' in column:
                default = column['default']

                if not default:
                    raise InvalidCSVColumnDefinition(
                        "Default value for column {0} is empty".format(
                            column_name))

                if 'choices' in column and default not in column['choices']:
                    raise InvalidCSVColumnDefinition(
                        "Default value for column {0} not in choices. "
                        "Expected {1}. Got {2}".format(
                            column_name, column['choices'], default))

                if 'validator' in column and not column['validator'](default):
                    raise InvalidCSVColumnDefinition(
                        "The default value of column {0} "
                        "doesn't validate".format(column_name))

    def _skip_lines(self):
        for i in range(0, self.skip_lines):
            try:
                next(self.reader)
            except StopIteration:
                raise AttributeError(
                    "Skip lines had an invalid argument")

    def _read_header(self):
        """Will skip blank lines"""
        for row in self.reader:
            if not self.is_empty_row(row):
                return row

    def _validate_header(self):
        csv_header = self.csv_header
        if self.strip_white_spaces:
            csv_header = [val.strip() for val in self.csv_header]

        if csv_header != self.model_fields:
            raise InvalidCSVHeaderException(
                "The header is invalid. Expected {0}. Got {1}".format(
                    self.model_fields, self.csv_header
                ))

    def __iter__(self):
        return self

    def _is_valid_row_length(self, row):
        if len(row) != len(self.model_fields):
            return False, {'row_length': 'Row length is invalid'}
        return True, {}

    def _is_valid_row_values(self, row):
        for value, column in zip(row, self.columns):
            if column.get('required', False) and not value:
                return False, {
                    column['name']: 'Field required and not provided.'
                }

            if value and not column.get('skip', False):
                if 'choices' in column and value not in column['choices']:
                    return False, {
                        column['name']: (
                            'Invalid choice. '
                            'Expected {0}. Got {1}'.format(
                                column['choices'], value))
                    }

                if 'validator' in column:
                    validator = column.get('validator')
                    if not validator(value):
                        return False, {column['name']: 'Validation failed'}
        return True, {}

    validity_checks = [_is_valid_row_length, _is_valid_row_values]

    def validate_row(self, row):
        for validity_check in self.validity_checks:
            valid, row_errors = validity_check(self, row)
            if not valid:
                return False, row_errors
        return True, {}

    def is_empty_row(self, csv_row):
        return (
            not csv_row or len(csv_row) == 0 or
            (len(csv_row) == 1 and not csv_row[0].strip())
        )

    def _add_error(self, csv_row,
                   row_counter, error_description=None):
        self.errors.setdefault('rows', {})
        row_error = {
            'row': csv_row,
            'errors': {
            }
        }
        if error_description:
            row_error['errors'].update(error_description)
        self.errors['rows'][row_counter] = row_error

    def _build_object(self, csv_row):
        obj = {}

        for value, column in zip(csv_row, self.columns):
            if column.get('skip', False):
                continue

            column_name = column.get('name')

            if value:
                value = (value.strip() if self.strip_white_spaces else value)

                if 'transform' in column:
                    try:
                        value = column['transform'](value)
                    except Exception as e:
                        raise CSVTransformException(
                            "Value transformed raised an exception",
                            original_exception=e)
            elif 'default' in column:
                value = column.get('default')

            obj[column_name] = value

        return obj

    def next_value(self):
        csv_row = next(self.reader)

        if self.is_empty_row(csv_row):
            return None

        valid, errors = self.validate_row(csv_row)

        if not valid:
            self.failure_count += 1
            if self.fail_fast or self.failure_count == self.max_failures:
                raise InvalidCSVException(
                    self.DEFAULT_ROW_INVALID_MESSAGE.format(self.row_counter),
                    errors)
            else:
                self._add_error(
                    csv_row, row_counter=self.row_counter,
                    error_description=errors)
                self.row_counter += 1
                return None

        try:
            obj = self._build_object(csv_row)
        except CSVTransformException as e:
            original_exception = e.original_exception
            if self.fail_fast:
                raise original_exception
            self._add_error(
                csv_row, self.row_counter,
                error_description={'transform': repr(original_exception)})
            self.row_counter += 1
            return None

        self.row_counter += 1
        return obj

    def __next__(self):
        val = None
        while val is None:
            val = self.next_value()
        return val

    next = __next__
