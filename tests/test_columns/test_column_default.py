import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ValidatorColumnTestCase(BaseSmartCSVTestCase):
    def test_required_column_empty_fails_even_with_default(self):
        """Should fail if the column is required and the value is empty."""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': ''
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '799'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True, 'default': 999},
        ])

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('price' in e.errors)

    def test_required_column_with_value_returns_original_value(self):
        """Should return the value provided and not the default"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': '699'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '799'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True, 'default': 999},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_not_required_column_empty_returns_default_value(self):
        """Should return the default value if no other is provided"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': ''
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '799'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': False, 'default': 999},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'price': 999
        })
        self.assertModelsEquals(ipad, ipad_data)

    def test_not_required_column_not_empty_returns_value(self):
        """Should return the value provided and not the default"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': '699'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '799'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': False, 'default': 999},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)
