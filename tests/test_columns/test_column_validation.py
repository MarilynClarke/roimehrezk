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
    def test_valid_value_is_provided(self):
        """Should be validated ok"""
        pass

    def test_invalid_value_is_passed_and_exception_is_raised(self):
        """Should not validate and raise a exception (fail_fast=True)"""
        pass

    def test_invalid_value_is_passed_and_no_exception_is_raised(self):
        """Should not validate and the error be reported on the reader"""
        pass

    def test_not_required_value_empty_is_not_validated(self):
        """Should not try to validate an empty value"""
        pass

    def test_not_required_value_empty_and_default_is_not_validated(self):
        """Should not try to validate the default value of an empty value"""
        pass
