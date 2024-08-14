import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import COLUMNS_1, is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class ValidValueTransformation(BaseSmartCSVTestCase):
    def test_required_column_with_data_is_transformed(self):
        """Should apply the transformation to the value"""
        pass

    def test_column_with_missing_data_is_not_transformed(self):
        """Shouldn't invoke the transform function if no value is passed"""
        pass

    def test_default_value_is_not_transformed(self):
        """Shouldn't apply no transformation if the value is missing and the default value is being used"""
        pass


class ErrorValueTransformationTestCase(BaseSmartCSVTestCase):
    def test_error_preserves_exception_with_fail_fast(self):
        """Should raise the exception that happens with the value transformation"""
        pass

    def test_error_exception_is_reported_without_fail_fast(self):
        """reader.errors should contain the exception that happenend with the value transformation"""
        pass
