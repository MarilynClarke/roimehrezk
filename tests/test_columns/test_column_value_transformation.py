import six
import mock
import decimal
from decimal import Decimal

if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..base import BaseSmartCSVTestCase

import smartcsv


class ValidValueTransformation(BaseSmartCSVTestCase):
    def test_required_column_with_data_is_transformed(self):
        """Should apply the transformation to the value"""
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
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'transform': lambda x: Decimal(x)
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'price': Decimal('799')
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'price': Decimal('699')
        })

    def test_column_with_missing_data_is_not_transformed(self):
        """Shouldn't invoke the transform function if no value is passed"""
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
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        mocked_validator = mock.MagicMock(return_value=True)
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': False,
                'transform': mocked_validator
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

        self.assertEqual(mocked_validator.call_count, 0)

    def test_default_value_is_not_transformed(self):
        """Shouldn't apply no transformation if the value is missing and the default value is being used"""
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
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        mocked_validator = mock.MagicMock(return_value=True)
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': False,
                'transform': mocked_validator,
                'default': 899
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'price': 899
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'price': 899
        })

        self.assertEqual(mocked_validator.call_count, 0)


class ErrorValueTransformationTestCase(BaseSmartCSVTestCase):
    def test_error_preserves_exception_with_fail_fast(self):
        """Should raise the exception that happens with the value transformation"""
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
{ipad_row}
""".format(
            iphone_row="{title},{price}".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'transform': lambda x: Decimal(x)
            },
        ])

        self.assertRaises(decimal.InvalidOperation, lambda: next(reader))

    def test_error_exception_is_reported_without_fail_fast(self):
        """reader.errors should contain the exception that happenend with the value transformation"""
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
{ipad_row}
""".format(
            iphone_row=iphone_row,
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'required': True,
                'transform': lambda x: Decimal(x)
            },
        ], fail_fast=False)

        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))
        self.assertTrue(isinstance(ipad, dict))
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'price': Decimal('699')
        })

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)
        self.assertEqual(len(reader.errors['rows']), 1)  # 1 row failing

        self.assertRowError(
            reader.errors, iphone_row, 0, 'transform')
