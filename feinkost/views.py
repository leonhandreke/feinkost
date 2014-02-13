import decimal
from datetime import datetime, timedelta
import re

from flask import render_template, request, redirect, url_for

from wtforms import fields
from wtforms.validators import ValidationError
from flask.ext.wtf import Form

from feinkost import app
from feinkost.forms import RedirectForm
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
def inventoryitem_add():
    try:
        product = Product.objects.get(barcode=request.args.get('barcode'))
    except Product.DoesNotExist:
        return redirect(url_for('product_create', barcode=request.args.get('barcode'), next=request.url))

    InventoryItem(category=product.category,
                  best_before=datetime.now() + timedelta(days=product.best_before_days),
                  quantity = product.quantity).save()

    return redirect(url_for('inventoryitem_list'))

class ProductForm(RedirectForm):
    barcode = fields.TextField()
    name = fields.TextField()
    trading_unit = fields.TextField()
    category = fields.TextField()
    best_before_days = fields.IntegerField()

    TRADING_UNIT_RE = '(\d+)(\w*)'

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
@app.route('/product/create', methods=['GET', 'POST'])
def product_create():
    form = ProductForm(request.values)
    if request.method == 'POST' and form.validate():
        product = Product(name=form.name.data,
                          best_before_days=form.best_before_days.data,
                          quantity=form.get_quantity(),
                          barcode=form.barcode.data)
        product.category, _ = ProductCategory.objects.get_or_create(name=form.category.data,
                                                                    unit=form.get_unit())
        product.save()

        return form.redirect('inventoryitem_list')
    else:
        return render_template('product_create.html', form=form)
