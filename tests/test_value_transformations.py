import csv
import six
from decimal import Decimal, InvalidOperation

if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .base import BaseSmartCSVTestCase
from .config import COLUMNS_WITH_VALUE_TRANSFORMATIONS

import smartcsv


class ValidCSVWithValueTransformations(BaseSmartCSVTestCase):
    def test_valid_and_value_transformed_with_all_data(self):
        """Should transform all values (in_stock) is not required but present"""
        csv_data = """
title,currency,price,in_stock
iPhone 5c blue,USD,799,yes
iPad mini,USD,699,no
"""
        reader = smartcsv.reader(
            StringIO(csv_data), columns=COLUMNS_WITH_VALUE_TRANSFORMATIONS)
        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': Decimal('799'),
            'in_stock': True
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'currency': 'USD',
            'price': Decimal('699'),
            'in_stock': False
        })

    def test_valid_and_value_transformed_with_only_required_data(self):
        """Should transform all values with only required data present"""
        csv_data = """
title,currency,price,in_stock
iPhone 5c blue,USD,799,
iPad mini,USD,699,
"""
        reader = smartcsv.reader(
            StringIO(csv_data), columns=COLUMNS_WITH_VALUE_TRANSFORMATIONS)
        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': Decimal('799'),
            'in_stock': ''
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini',
            'currency': 'USD',
            'price': Decimal('699'),
            'in_stock': ''
        })


class InvalidCSVWithValueTransformations(BaseSmartCSVTestCase):
    def setUp(self):
        self.columns = COLUMNS_WITH_VALUE_TRANSFORMATIONS[:]
        price_without_validation = self.columns[2].copy()
        del price_without_validation['validator']
        self.columns[2] = price_without_validation

    def test_invalid_value_causes_natural_exception(self):
        """Should raise the exception raised by the transform function"""
        csv_data = """
title,currency,price,in_stock
iPhone 5c blue,USD,799,
iPad mini,USD,INVALID,
"""
        reader = smartcsv.reader(StringIO(csv_data), columns=self.columns)
        iphone = next(reader)

        self.assertRaises(InvalidOperation, lambda: next(reader))

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(
            isinstance(iphone, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': Decimal('799'),
            'in_stock': ''
        })

    def test_invalid_value_with_fail_fast_deactivated(self):
        """Shouldn't raise the exception raised by the transform function but save it in the errors attribute"""
        invalid_row = "iPad mini,USD,INVALID,"
        csv_data = """
title,currency,price,in_stock
iPhone 5c blue,USD,799,
{invalid_row}
Macbook Pro,USD,1399,yes
{invalid_row}
iPod shuffle,USD,199,
""".format(invalid_row=invalid_row)
        reader = smartcsv.reader(
            StringIO(csv_data), columns=self.columns, fail_fast=False)
        iphone = next(reader)
        mac = next(reader)
        ipod = next(reader)

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5c blue',
            'currency': 'USD',
            'price': Decimal('799'),
            'in_stock': ''
        })
        self.assertModelsEquals(mac, {
            'title': 'Macbook Pro',
            'currency': 'USD',
            'price': Decimal('1399'),
            'in_stock': True
        })
        self.assertModelsEquals(ipod, {
            'title': 'iPod shuffle',
            'currency': 'USD',
            'price': Decimal('199'),
            'in_stock': ''
        })

        self.assertTrue(reader.errors is not None)
        self.assertTrue('rows' in reader.errors)
        self.assertTrue(1 in reader.errors['rows'])
        self.assertTrue(3 in reader.errors['rows'])

        self.assertTrue('transform' in reader.errors['rows'][1]['errors'])
        self.assertTrue(
            'InvalidOperation' in
            reader.errors['rows'][1]['errors']['transform'])

        self.assertTrue('transform' in reader.errors['rows'][3]['errors'])
        self.assertTrue(
            'InvalidOperation' in
            reader.errors['rows'][3]['errors']['transform'])

        self.assertRowError(reader.errors, invalid_row, 1, 'transform')
