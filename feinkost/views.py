import decimal
import re

from flask import render_template, request, redirect, url_for

from wtforms import fields
from wtforms.validators import ValidationError
from flask_wtf import Form

from feinkost import app
from feinkost.models import InventoryItem, Product, ProductCategory

@app.route('/')
def inventoryitem_list():
    items = []
    for item in InventoryItem.objects:
        items.append({
            'title': item.category.name,
            'quantity': item.quantity,
            'unit': item.get_unit(),
            'best_before': item.best_before
            })

    return render_template('inventoryitem_list.html', inventory_items=items)

@app.route('/inventoryitem/add')
@app.route('/inventoryitem/add/<barcode>')
def inventoryitem_add(barcode=None):
    try:
        product = Product.objects.get(barcode=barcode)
    except Product.DoesNotExist:
        return redirect(url_for('product_create', barcode=barcode))


class ProductForm(Form):
    name = fields.TextField()
    trading_unit = fields.TextField()
    category = fields.TextField()
    best_before_days = fields.IntegerField()

    TRADING_UNIT_RE = '(\d+)(\W*)'

    def validate_quantity(self, field):
        trading_unit_re = re.search(self.TRADING_UNIT_RE, field.data)
        if not trading_unit_re:
            raise ValidationError("Invalid trading unit format.")

        product_category = ProductCategory.objects.filter(name=self.category.data).first()
        if product_category and not product_category.unit == self.get_unit():
            raise ValidationError("Unit does not match product category's unit.")

    def get_unit(self):
        trading_unit_re = re.search(self.TRADING_UNIT_RE, self.trading_unit.data)
        return trading_unit_re.group(2)

    def get_quantity(self):
        trading_unit_re = re.search(self.TRADING_UNIT_RE, self.trading_unit.data)
        return int(trading_unit_re.group(1))


#@app.route('/product/create')
@app.route('/product/create/<barcode>', methods=['GET', 'POST'])
def product_create(barcode=None):
    form = ProductForm()
    if request.method == 'POST' and form.validate():
        product = Product(name=form.name.data,
                          best_before_days=form.best_before_days.data,
                          quantity=form.get_quantity(),
                          barcode=barcode)
        product.category, _ = ProductCategory.objects.get_or_create(name=form.category.data,
                                                                    unit=form.get_unit())
        product.save()
        # TODO: Redirect back to the inventoryitem add form if needed.
        return redirect('/')
    else:
        return render_template('product_create.html', form=form, barcode=barcode)
