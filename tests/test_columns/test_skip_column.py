import six
import mock
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

import smartcsv

from ..base import BaseSmartCSVTestCase


class SkipColumnTestCase(BaseSmartCSVTestCase):
    def test_skip_column_doesnt_return_the_value(self):
        """Should return the object without the skipped column"""
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
                'skip': True
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C'
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini'
        })

    def test_skip_column_doesnt_invoke_validator(self):
        """Should return the object without the skipped column"""
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
        mocked_validator = mock.MagicMock(return_value=True)
        reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'title', 'required': True},
            {
                'name': 'price',
                'validator': mocked_validator,
                'skip': True
            },
        ])

        iphone = next(reader)
        ipad = next(reader)

        self.assertRaises(StopIteration, lambda: list(next(reader)))

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, {
            'title': 'iPhone 5C'
        })
        self.assertModelsEquals(ipad, {
            'title': 'iPad mini'
        })

        self.assertEqual(mocked_validator.call_count, 0)
