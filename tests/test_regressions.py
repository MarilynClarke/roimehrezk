import csv
import six

if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .base import BaseSmartCSVTestCase
from .config import CURRENCY_CHOICES, is_number

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ChoicesNotRequiredTestCase(BaseSmartCSVTestCase):
    """Bug introduced in the first version. If a column was not required
    but it was a choice field it was always marked as invalid."""
    def test_choice_field_is_valid_if_all_optional_choices_are_missing(self):
        """Should validate models without currencies if the field is optional"""
        csv_data = """
title,currency,price
iPhone 5c blue,,799
iPad mini,,699
        """
        columns = [
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': False,
                'choices': CURRENCY_CHOICES
            },
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            }
        ]

        reader = smartcsv.reader(StringIO(csv_data), columns=columns)

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': '',
            'price': '799'
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'currency': '',
            'price': '699'
        })

    def test_choice_field_is_valid_if_some_optional_choices_are_missing(self):
        """Should validate models without currencies if the field is optional"""
        csv_data = """
title,currency,price
iPhone 5c blue,USD,799
iPad mini,,699
        """
        columns = [
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': False,
                'choices': CURRENCY_CHOICES
            },
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            }
        ]

        reader = smartcsv.reader(StringIO(csv_data), columns=columns)

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': '799'
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'currency': '',
            'price': '699'
        })

    def test_choice_field_is_required_and_missing_value_is_invalid(self):
        """Should fail to validate if a required choice field is missing"""
        csv_data = """
    title,currency,price
    iPhone 5c blue,USD,799
    iPad mini,,699
            """
        columns = [
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            },
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            }
        ]

        reader = smartcsv.reader(StringIO(csv_data), columns=columns)

        iphone = next(reader)
        self.assertRaises(InvalidCSVException, lambda: next(reader))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': '799'
        })
