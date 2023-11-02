# Smart and awesome CSV utils

**CSVs are awesome, yet they're pretty dumb. Let's get them smarter!**

smartcsv is a python utility to read and parse CSVs based on model definitions. Instead of just parsing the CSV into lists (like the builtin `csv` module) it adds the ability to specify models with attributes names. On top of that it adds nice features like validation, custom parsing, failure control and nice error messages.

### Installation
    pip install smartcsv

### Usage

To see an entire set of usages check the `test` package (99% coverage).

The basic is to define a spec for the columns of your csv. Assuming the following CSV file:

    title,category,subcategory,currency,price,url,image_url
    iPhone 5c blue,Phones,Smartphones,USD,399,http://apple.com/iphone,http://apple.com/iphone.jpg
    iPad mini,Tablets,Apple,USD,699,http://apple.com/iphone,http://apple.com/iphone.jpg

First you need to define the spec for your columns. This is an example (the one used in `tests`):

```python
COLUMNS_1 = [
    {'name': 'title', 'required': True},
    {'name': 'category', 'required': True},
    {'name': 'subcategory', 'required': False},
    {
        'name': 'currency',
        'required': True,
        'choices': CURRENCIES
    },
    {
        'name': 'price',
        'required': True,
        'validator': is_number
    },
    {
        'name': 'url',
        'required': True,
        'validator': lambda c: c.startswith('http')
    },
    {
        'name': 'image_url',
        'required': False,
        'validator': lambda c: c.startswith('http')
    },
]
```

You can then use `smartcsv` to parse the CSV:

```python
import smartcsv
with open('my-csv.csv', 'r') as f:
    reader = smartcsv.reader(f, columns=COLUMNS_1)
    for obj in reader:
        print(obj['title'])
```