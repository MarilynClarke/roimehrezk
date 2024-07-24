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
        self.errors = {'rows': {}}

        self.model_fields = [c['name'] for c in self.columns]

        self._skip_lines()

        if header_included:
            self.csv_header = self._read_header()
            self._validate_header()

    def _skip_lines(self):
        for i in range(0, self.skip_lines):
            try:
                next(self.reader)
            except StopIteration:
                raise InvalidCSVArgumentException(
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
        for index, value in enumerate(row):
            column = self.columns[index]
            if column.get('required', False) and not value:
                return False, {
                    column['name']: 'Field required and not provided.'
                }

            if 'choices' in column:
                if value and value not in column['choices']:
                    return False, {
                        column['name']: (
                            'Invalid choice. '
                            'Expected {0}. Got {1}'.format(column['choices'], value))
                    }

            if 'validator' in column and value:
                validator = column.get('validator')
                if not hasattr(validator, '__call__'):
                    raise AttributeError(
                        "The validator for column {0} is not callable".format(
                            column['name']))
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

    def _get_column_by_name(self, name):
        for column in self.columns:
            if name == column.get('name'):
                return column

    def _add_error(self, error_dict, csv_row,
                   row_counter, error_description=None):
        row_error = {
            'row': csv_row,
            'errors': {
            }
        }
        if error_description:
            row_error['errors'].update(error_description)
        error_dict['rows'][row_counter] = row_error

    def __next__(self):
        csv_row = next(self.reader)

        if self.is_empty_row(csv_row):
            return next(self)

        valid, errors = self.validate_row(csv_row)

        if not valid:
            self.failure_count += 1
            if self.fail_fast or self.failure_count == self.max_failures:
                raise InvalidCSVException(
                    self.DEFAULT_ROW_INVALID_MESSAGE.format(self.row_counter),
                    errors)
            else:

                self._add_error(
                    self.errors, csv_row,
                    row_counter=self.row_counter, error_description=errors)
                self.row_counter += 1
                return next(self)

        obj = {}

        for index, csv_value in enumerate(csv_row):

            if self.columns[index].get('skip', False):
                continue

            csv_value = (csv_value.strip() if
                         self.strip_white_spaces else csv_value)

            column_name = self.model_fields[index]
            column = self._get_column_by_name(column_name)

            value = csv_value

            if 'transform' in column:
                try:
                    value = column['transform'](csv_value)
                except Exception as e:
                    if self.fail_fast:
                        raise e
                    self._add_error(
                        self.errors, csv_row, self.row_counter,
                        error_description={'transform': repr(e)})
                    self.row_counter += 1
                    return next(self)

            obj[column_name] = value

        self.row_counter += 1
        return obj

    next = __next__
