import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ValidRequiredColumnTestCase(BaseSmartCSVTestCase):
    def test_required_value_is_provided(self):
        """Shouldn't fail and return the correct value"""
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
            {'name': 'price', 'required': True},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_not_required_value_is_not_provided(self):
        """Shouldn't fail and should have an empty value"""
        iphone_data = {
            'title': 'iPhone 5C'
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
            iphone_row="{title},".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': False},
            {'name': 'price', 'required': False},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'price': ''
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'price': ''
        })

    def test_not_required_value_is_provided(self):
        """Shouldn't fail and should have an the correct value"""
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
            {'name': 'title', 'required': False},
            {'name': 'price', 'required': False},
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)


class InvalidRequiredColumnTestCase(BaseSmartCSVTestCase):
    def test_required_value_is_missing_and_fail_fast(self):
        """Should fail fast and report the error"""
        iphone_data = {
            'title': 'iPhone 5C'
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
            iphone_row="{title},".format(**iphone_data),
            ipad_row="{title},{price}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {'name': 'price', 'required': True},
        ])

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('price' in e.errors)
        else:
            assert False, "Shouldn't reach this state"

    def test_required_value_is_missing_and_dont_fail_fast(self):
        """Shouldn't fail fast, instead report errors on reader.errors"""
        iphone_data = {
            'title': 'iPhone 5C'
        }
        ipad_data = {
            'title': 'iPad mini',
            'price': '699'
        }
        iphone_row = "{title},".format(**iphone_data)
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
            {'name': 'price', 'required': True},
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
