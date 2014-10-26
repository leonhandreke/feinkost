from urllib.parse import urlparse, urljoin
import re
from decimal import Decimal

from flask import request, url_for, redirect
from flask.ext.wtf import Form
from wtforms import SelectField, HiddenField, TextField, StringField
from wtforms.validators import StopValidation

from feinkost.models import ProductCategory
from feinkost import constants

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    target = request.args.get('next')
    if is_safe_url(target):
        return target


class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))

class ProductCategoryField(StringField):

    def process_data(self, product_category):
        self.data = getattr(product_category, 'name', '')

    def populate_obj(self, obj, name):
        setattr(obj, name, ProductCategory.objects.get(name=self.data))

class QuantityUnitField(TextField):

    TRADING_UNIT_RE = '(\d+\.?\d*)([a-zA-Z]*)'

    def pre_validate(self, form):
        match = re.search(self.TRADING_UNIT_RE, self.data)
        if not match:
            raise StopValidation("Invalid quantity format.")

        unit = match.group(2)

        if unit not in constants.UNITS:
            raise StopValidation("Invalid unit.")

    def get_trading_unit(self):
        match = re.search(self.TRADING_UNIT_RE, self.data)
        quantity = Decimal(match.group(1))
        unit = match.group(2)

        return (quantity, unit)
