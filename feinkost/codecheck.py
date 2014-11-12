from decimal import Decimal
import re
import requests

TRADING_UNIT_RE = '(\d+\.?\d*)(\w*)'

def get_product_data_by_barcode(barcode):
    """Get product information for a barcode form the website codecheck.info

    Args:
        barcode: str, the barcode to search for.
    Returns:
        A dictionary with:
            name, str
            category, str
            quantity, Decimal
            unit: str
    """
    url = 'http://www.codecheck.info/WebService/rest/prod/ean2/1/256/' + barcode
    headers = {
        'Authorization': 'DigestQuick nonce="kbfc2IH6wtwLZBkUlE4iUA==",mac="whHjv8BU97fipOIs0pa5qOMfpSih/sxINshh0Xr9hXg="'
    }
    prod_id = requests.get(url, headers=headers).json()['result']['id']

    url = 'http://www.codecheck.info/WebService/rest/prod/id/5422089/' + str(prod_id)

    r = requests.get(url, headers=headers).json()['result']

    name = r['name']
    category = r.get('catName', '')
    trading_unit = r.get('quant', '')

    trading_unit = (trading_unit.replace(' ', '')
                    # Remove Germany 1000-separators
                    .replace('.', '')
                    # Convert German decimal separators
                    .replace(',', '.')
                    .replace('Liter', 'l')
                    .lower())

    match = re.match(TRADING_UNIT_RE, trading_unit)
    if match:
        quantity = Decimal(match.group(1))
        unit = match.group(2)
    else:
        unit = ''
        quantity = ''

    return {
        'name': name,
        'category': category,
        'quantity': quantity,
        'unit': unit
    }
