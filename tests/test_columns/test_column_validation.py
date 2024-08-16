import six
import mock
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ValidatorColumnTestCase(BaseSmartCSVTestCase):
    def test_valid_value_is_provided(self):
        """Should be validated ok"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': '799'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '699'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_invalid_value_is_passed_and_exception_is_raised(self):
        """Should not validate and raise a exception (fail_fast=True)"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': 'INVALID'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '699'
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            },
        ])

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('price' in e.errors)

    def test_invalid_value_is_passed_and_no_exception_is_raised(self):
        """Should not validate and the error be reported on the reader"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': 'INVALID'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '699'
        }
        iphone_row = "{title},{price}".format(**iphone_data)

        csv_data = """
title,price
{iphone_row}
{ipad_row}""".format(
            iphone_row=iphone_row,
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'validator': is_number
            },
        ], fail_fast=False)

        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))
        self.assertTrue(isinstance(ipad, dict))
        self.assertModelsEquals(ipad, ipad_data)

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)
        self.assertEqual(len(reader.errors['rows']), 1)  # 1 row failing

        self.assertRowError(
            reader.errors, iphone_row, 0, 'price')

    def test_not_required_value_empty_is_not_validated(self):
        """Should not try to validate an empty value"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': ''
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': ''
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )

        mocked_validator = mock.MagicMock(return_value=True)
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': False,
                'validator': mocked_validator
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

        self.assertEqual(mocked_validator.call_count, 0)

    def test_default_value_is_not_validated(self):
        """Should not try to validate the default value of an empty column"""
        iphone_data = {
            'title': 'iPhone 5C',
            'price': ''
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': ''
        }
        csv_data = """
title,price
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )

        mocked_validator = mock.MagicMock(return_value=True)
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': False,
                'default': 999,
                'validator': mocked_validator
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'price': 999
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'price': 999
        })

        # Just the model definition
        self.assertEqual(mocked_validator.call_count, 1)
