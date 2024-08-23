import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .base import BaseSmartCSVTestCase
from .config import CURRENCY_CHOICES, is_number

import smartcsv
from smartcsv.exceptions import InvalidCSVColumnDefinition


CSV_DATA = """
iPhone 5c, 799
iPad mini, 699
"""


class InvalidModelDefinitionsTestCase(BaseSmartCSVTestCase):
    def test_column_doesnt_have_a_name(self):
        """Should fail if a column doesn't have a name"""
        columns = [
            {'required': True},
            {'name': 'price', 'required': True},
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))

    def test_names_are_repeated(self):
        """Should fail a names are repeated"""
        columns = [
            {'name': 'title', 'required': True},
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True},
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))

    def test_column_validator_is_not_callable(self):
        """Should fail a validator is not callable"""
        columns = [
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True, 'validator': '8'},
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))

    def test_default_value_is_empty(self):
        """Should fail a default value is empty"""
        columns = [
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True, 'default': ''},
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))

    def test_default_value_not_in_choices(self):
        """Should fail if the default value not in choices"""
        columns = [
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'choices': CURRENCY_CHOICES,
                'default': 'INVALID'
            },
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))

    def test_default_value_doesnt_validate(self):
        """Should fail if the default value doesn't validate"""
        columns = [
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'validator': is_number,
                'default': 'INVALID'
            },
        ]
        self.assertRaises(
            InvalidCSVColumnDefinition,
            lambda: smartcsv.reader(StringIO(CSV_DATA), columns=columns,
                                    header_included=False))
