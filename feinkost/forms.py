from urllib.parse import urlparse, urljoin
import re
from decimal import Decimal

from flask import request, url_for, redirect
from flask.ext.wtf import Form
from wtforms import SelectField, HiddenField, TextField
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

class ProductCategoryField(SelectField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = ProductCategory.objects.all().scalar('id', 'name')
        super(ProductCategoryField, self).__init__(*args, **kwargs)

    def process_data(self, product_category):
        self.data = self.coerce(product_category.id)

    def pre_validate(self, form):
        try:
            ProductCategory.objects.get(id=self.data)
        except ProductCategory.DoesNotExist as e:
            raise StopValidation(e.args[0])

    def populate_obj(self, obj, name):
        setattr(obj, name, ProductCategory.objects.get(id=self.data))


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
