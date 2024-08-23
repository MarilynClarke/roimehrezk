import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import CURRENCY_CHOICES
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException


class ValidChoicesTestCase(BaseSmartCSVTestCase):
    def test_valid_choice_is_provided(self):
        """Should not fail and have the value of the selected choice"""
        iphone_data = {
            'title': 'iPhone 5C',
            'currency': 'USD'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{currency}".format(**iphone_data),
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            }
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_column_optional_and_choice_missing(self):
        """Shouldn't fail and have an empty value"""
        iphone_data = {
            'title': 'iPhone 5C'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},".format(**iphone_data),
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': False,
                'choices': CURRENCY_CHOICES
            }
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'currency': ''
        })
        self.assertModelsEquals(ipad, ipad_data)

    def test_choice_has_a_default_value(self):
        """Shouldn't fail and use the default value for a choice"""
        iphone_data = {
            'title': 'iPhone 5C',
            'currency': ''
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{currency}".format(**iphone_data),
            ipad_row="{title},{currency}".format(**ipad_data)
        )

        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': False,
                'choices': CURRENCY_CHOICES,
                'default': 'USD',
            }
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C',
            'currency': 'USD'
        })
        self.assertModelsEquals(ipad, ipad_data)


class InvalidChoicesTestCase(BaseSmartCSVTestCase):
    def test_invalid_choice_is_provided_with_fail_fast(self):
        """Should fail because the choice is invalid"""
        iphone_data = {
            'title': 'iPhone 5C',
            'currency': 'INVALID'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},{currency}".format(**iphone_data),
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            }
        ])

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('currency' in e.errors)
        else:
            assert False, "Shouldn't reach this state"

    def test_column_required_and_choice_missing_with_fail_fast(self):
        """Should fail because the field is required"""
        iphone_data = {
            'title': 'iPhone 5C'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row="{title},".format(**iphone_data),
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            }
        ])

        try:
            next(reader)
        except InvalidCSVException as e:
            self.assertTrue(e.errors is not None)
            self.assertTrue('currency' in e.errors)
        else:
            assert False, "Shouldn't reach this state"

    def test_invalid_choice_is_provided_without_fail_fast(self):
        """Should report invalid choice error on reader.errors"""
        iphone_data = {
            'title': 'iPhone 5C',
            'currency': 'INVALID'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        iphone_row = "{title},{currency}".format(**iphone_data)
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row=iphone_row,
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            }
        ], fail_fast=False)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: next(reader))
        self.assertTrue(isinstance(ipad, dict))
        self.assertModelsEquals(ipad, ipad_data)

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)
        self.assertEqual(len(reader.errors['rows']), 1)  # 1 row failing

        self.assertRowError(
            reader.errors, iphone_row, 0, 'currency')

    def test_column_required_and_choice_missing_without_fail_fast(self):
        """Should report required choice missing error on reader.errors"""
        iphone_data = {
            'title': 'iPhone 5C'
        }
        ipad_data = {
            'title': 'iPad mini',
            'currency': 'ARS'
        }
        iphone_row = "{title},".format(**iphone_data)
        csv_data = """
title,currency
{iphone_row}
{ipad_row}""".format(
            iphone_row=iphone_row,
            ipad_row="{title},{currency}".format(**ipad_data)
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'currency',
                'required': True,
                'choices': CURRENCY_CHOICES
            }
        ], fail_fast=False)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: next(reader))
        self.assertTrue(isinstance(ipad, dict))
        self.assertModelsEquals(ipad, ipad_data)

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)
        self.assertEqual(len(reader.errors['rows']), 1)  # 1 row failing

        self.assertRowError(
            reader.errors, iphone_row, 0, 'currency')
