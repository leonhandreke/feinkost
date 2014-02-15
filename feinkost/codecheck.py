import re
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

def get_product_data_by_barcode(barcode):
    search_url = 'http://www.codecheck.info/product.search?q=' + urllib.parse.quote(str(barcode))
    response = urllib.request.urlopen(search_url)

    # If nothing specific was found the website does not redirect
    if response.geturl() == search_url:
        return None

    soup = BeautifulSoup(response.read())

    breadcrumbs = soup.find(class_='breadcrumb').find_all('a')
    product_name = breadcrumbs[-1].string
    product_category = breadcrumbs[-2].string

    trading_unit_str = soup.find(text=re.compile("Menge")).parent.next_sibling.contents[0].string
    trading_unit_re = re.search('(\d+)\s*(\w*)', trading_unit_str)
    quantity = trading_unit_re.group(1)
    unit = trading_unit_re.group(2)

    return {
        'name': product_name,
        'category': product_category,
        'quantity': quantity,
        'unit': unit
    }
