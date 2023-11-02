CURRENCIES = ['USD', 'ARS', 'JPY']


def is_number(n):
    try:
        float(n)
        return True
    except ValueError:
        return False


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

IPHONE_DATA = {
    'category': 'Phones',
    'currency': 'USD',
    'image_url': 'http://apple.com/iphone.jpg',
    'price': '699',
    'subcategory': 'Smartphones',
    'title': 'iPhone 5c blue',
    'url': 'http://apple.com/iphone'
}

IPAD_DATA = {
    'category': 'Tablets',
    'currency': 'USD',
    'image_url': 'http://apple.com/ipad.jpg',
    'price': '599',
    'subcategory': 'Apple',
    'title': 'iPad mini',
    'url': 'http://apple.com/ipad'
}

VALID_TEMPLATE_STR = ("{title},{category},{subcategory},{currency},"
                      "{price},{url},{image_url}")