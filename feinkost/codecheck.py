from decimal import Decimal
import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

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
    search_url = 'http://www.codecheck.info/product.search?q=' + urllib.parse.quote(str(barcode))
    response = urllib.request.urlopen(search_url)

    # If nothing specific was found the website does not redirect
    if response.geturl() == search_url:
        return None

    soup = BeautifulSoup(response.read())

    breadcrumbs = soup.find(class_='breadcrumb').find_all('a')
    product_name = breadcrumbs[-1].string
    product_category = breadcrumbs[-2].string

    trading_unit = soup.find(text=re.compile("Menge")).parent.next_sibling.next_sibling.string
    trading_unit = (trading_unit.replace(' ', '')
                    # Remove Germany 1000-separators
                    .replace('.', '')
                    # Convert German decimal separators
                    .replace(',', '.'))

    trading_unit_re = re.search('(\d+\.*\d*)(\w*)', trading_unit)
    quantity = Decimal(trading_unit_re.group(1))

    unit = trading_unit_re.group(2)
    if unit == "Liter":
        unit = 'l'
    unit = unit.lower()

    return {
        'name': product_name,
        'category': product_category,
        'quantity': quantity,
        'unit': unit
    }
