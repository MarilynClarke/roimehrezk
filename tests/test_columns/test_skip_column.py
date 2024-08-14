import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from ..config import COLUMNS_1, is_number
from ..base import BaseSmartCSVTestCase

import smartcsv
from smartcsv.exceptions import InvalidCSVException, InvalidCSVHeaderException


class SkipColumnTestCase(BaseSmartCSVTestCase):
    def test_skip_column_doesnt_return_the_value(self):
        """Should return the object without the skipped column"""
        pass