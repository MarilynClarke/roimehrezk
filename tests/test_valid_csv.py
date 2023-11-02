import six
if six.PY3:
    from io import StringIO
else:
    from StringIO import StringIO
from .base import BaseSmartCSVTestCase
from .config import COLUMNS_1, IPHONE_DATA, IPAD_DATA, VALID_TEMPLATE_STR


import smartcsv


class ValidCSVWithHeaderTestCase(BaseSmartCSVTestCase):
    def assertModelsEquals(self, model1, model2):
        for k, v in model1.items():
            self.assertEqual(v, model2[k])

    def test_valid_csv_with_all_data_and_header(self):
        """Should be valid if all data is passed"""
        csv_data = """
title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA),
        )

        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, IPHONE_DATA)
        self.assertModelsEquals(ipad, IPAD_DATA)

    def test_valid_csv_with_blank_lines(self):
        """Should be valid even if there are blank lines"""
        csv_data = """

title,category,subcategory,currency,price,url,image_url


{iphone_data}

{ipad_data}


        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA),
        )

        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, IPHONE_DATA)
        self.assertModelsEquals(ipad, IPAD_DATA)

    def test_valid_and_white_spaces_for_values_are_stripped(self):
        """Should strip white spaces out of values by default"""
        csv_data = """
    title,category,subcategory,currency,price,url,image_url
    {iphone_data}
    {ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**IPHONE_DATA),
            ipad_data=VALID_TEMPLATE_STR.format(**IPAD_DATA),
        )

        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, IPHONE_DATA)
        self.assertModelsEquals(ipad, IPAD_DATA)

    def test_valid_and_white_spaces_for_values_are_not_stripped(self):
        """Should strip white spaces out of values"""
        iphone_data = IPHONE_DATA.copy()
        ipad_data = IPAD_DATA.copy()

        iphone_data['category'] = "     Phones   "
        ipad_data['price'] = " 599  "

        csv_data = """
title,category,subcategory,currency,price,url,image_url
    {iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**iphone_data),
            ipad_data=VALID_TEMPLATE_STR.format(**ipad_data),
        )
        reader = smartcsv.reader(
            StringIO(csv_data), columns=COLUMNS_1, strip_white_spaces=False)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(
            isinstance(iphone, dict) and isinstance(ipad, dict))

        # First 4 spaces
        iphone_data['title'] = "    " + iphone_data['title']
        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_valid_csv_only_with_required_data(self):
        """Should be valid if only required data is passed"""
        iphone_data = IPHONE_DATA.copy()
        ipad_data = IPAD_DATA.copy()
        iphone_data['subcategory'] = ""
        iphone_data['image_url'] = ""

        ipad_data['subcategory'] = ""
        ipad_data['image_url'] = ""
        csv_data = """
title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**iphone_data),
            ipad_data=VALID_TEMPLATE_STR.format(**ipad_data),
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_valid_csv_with_different_choices(self):
        """All choices for a field should be valid"""
        iphone_data = IPHONE_DATA.copy()
        ipad_data = IPAD_DATA.copy()
        iphone_data['subcategory'] = ""
        iphone_data['image_url'] = ""

        ipad_data['subcategory'] = ""
        ipad_data['image_url'] = ""
        ipad_data['currency'] = "ARS"
        csv_data = """
title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**iphone_data),
            ipad_data=VALID_TEMPLATE_STR.format(**ipad_data),
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)
        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertModelsEquals(iphone, iphone_data)
        self.assertModelsEquals(ipad, ipad_data)

    def test_valid_csv_with_some_fields_not_required_empty(self):
        """Should be valid if some not required fields are filled and others don't"""

        iphone_data = IPHONE_DATA.copy()
        ipad_data = IPAD_DATA.copy()

        iphone_data['subcategory'] = ""
        iphone_data['image_url'] = ""

        ipad_data['image_url'] = ""

        csv_data = """
        title,category,subcategory,currency,price,url,image_url
{iphone_data}
{ipad_data}
        """.format(
            iphone_data=VALID_TEMPLATE_STR.format(**iphone_data),
            ipad_data=VALID_TEMPLATE_STR.format(**ipad_data),
        )
        reader = smartcsv.reader(StringIO(csv_data), columns=COLUMNS_1)
        iphone = next(reader)
        ipad = next(reader)

        with self.assertRaises(StopIteration):
            next(reader)

        self.assertTrue(isinstance(iphone, dict) and isinstance(ipad, dict))

        self.assertEqual(iphone['title'], 'iPhone 5c blue')
        self.assertEqual(ipad['title'], 'iPad mini')
        self.assertEqual(iphone['subcategory'], '')
        self.assertEqual(ipad['subcategory'], 'Apple')