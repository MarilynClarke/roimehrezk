import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import COLUMNS_1, is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class ValidRequiredColumnTestCase(BaseSmartCSVTestCase):
    def test_required_value_is_provided(self):
        """Shouldn't fail and return the correct value"""
        pass

    def test_not_required_value_is_not_provided(self):
        """Shouldn't fail and should have an empty value"""
        pass

    def test_not_required_value_is_provided(self):
        """Shouldn't fail and should have an the correct value"""
        pass


class InvalidRequiredColumnTestCase(BaseSmartCSVTestCase):
    def test_required_value_is_missing_and_fail_fast(self):
        """Should fail fast and report the error"""
        pass

    def test_required_value_is_missing_and_dont_fail_fast(self):
        """Shouldn't fail fast, instead report errors on reader.errors"""
        pass