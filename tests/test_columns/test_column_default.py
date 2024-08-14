import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import COLUMNS_1, is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class ValidatorColumnTestCase(BaseSmartCSVTestCase):
    def test_required_column_empty_returns_default_value(self):
        """Should return the default value if no other is provided"""
        pass

    def test_required_column_with_value_returns_original_value(self):
        """Should return the value provided and not the default"""
        pass

    def test_not_required_column_empty_returns_default_value(self):
        """Should return the default value if no other is provided"""
        pass

    def test_not_required_column_not_empty_returns_value(self):
        """Should return the value provided and not the default"""
        pass

    def test_fail_to_create_reader_if_default_value_not_in_choices(self):
        """Should raise an exception when the reader is created if the value is not part of the choices"""
        pass

    def test_fail_to_create_reader_if_default_value_doesnt_validate(self):
        """Should raise an exception when the reader is created if the value is does not validate"""
        pass

    def test_fail_to_create_reader_if_default_value_is_empty(self):
        """Should raise an exception when the reader is created if the default value is empty"""
        pass
