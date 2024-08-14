import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import COLUMNS_1, is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class ValidChoicesTestCase(BaseSmartCSVTestCase):
    def test_valid_choice_is_provided(self):
        """Should not fail and have the value of the selected choice"""
        pass

    def test_column_optional_and_choice_missing(self):
        """Shouldn't fail and have an empty value"""
        pass

    def test_choice_is_required_and_has_a_default_value(self):
        """Shouldn't fail and use the default"""
        pass


class InvalidChoicesTestCase(BaseSmartCSVTestCase):
    def test_invalid_choice_is_provided_with_fail_fast(self):
        """Should fail because the choice is invalid"""
        pass

    def test_column_required_and_choice_missing_with_fail_fast(self):
        """Should fail because the field is required"""
        pass

    def test_invalid_choice_is_provided_without_fail_fast(self):
        """Should report invalid choice error on reader.errors"""
        pass

    def test_column_required_and_choice_missing_without_fail_fast(self):
        """Should report required choice missing error on reader.errors"""
        pass