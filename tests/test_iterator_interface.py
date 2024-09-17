import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO

from .base import BaseSmartCSVTestCase
import smartcsv


class InvalidModelDefinitionsTestCase(BaseSmartCSVTestCase):
    def setUp(self):
        csv_data = """
id,name
1,john
2,mary"""
        self.reader = smartcsv.reader(StringIO(csv_data), columns=[
            {'name': 'id', 'required': True},
            {'name': 'name', 'required': True},
        ])

    def test_reader_container_is_itself_an_iterator(self):
        """reader container should be an iterator itself"""
        self.assertEqual(iter(self.reader), self.reader)

    def test_reader_has_a_python26_next_method(self):
        """Should have a next() method for Python 2.6 compatibility"""
        self.assertTrue(hasattr(self.reader, 'next'))
        self.assertTrue(self.reader.next(), {
            'id': '1',
            'name': 'john'
        })

    def test_reader_has_a_python27plus_next_method(self):
        """Should have a __next__() method for Python 2.7+ compatibility"""
        self.assertTrue(hasattr(self.reader, 'next'))
        self.assertTrue(self.reader.__next__(), {
            'id': '1',
            'name': 'john'
        })
