import decimal
from datetime import datetime, timedelta
import re
import urllib.parse

from flask import render_template, request, redirect, url_for, abort

from wtforms import fields
from wtforms.validators import ValidationError
from flask.ext.wtf import Form
from flask.ext.wtf import html5 as html5_fields

from feinkost import app
from feinkost import codecheck
from feinkost.forms import RedirectForm
from feinkost.models import InventoryItem, Product, ProductCategory

@app.route('/')
def inventoryitem_list():
    return render_template('inventoryitem_list.html', inventory_items=InventoryItem.objects,
                           abs=abs, int=int)

@app.route('/inventoryitem/add')
def inventoryitem_add():
    if 'barcode' not in request.args:
        return scan_barcode(url_for('inventoryitem_add', barcode=BARCODE_PLACEHOLDER, _external=True))

    # FIXME: GET modification is evil
    try:
        product = Product.objects.get(barcode=request.args.get('barcode'))
    except Product.DoesNotExist:
        return redirect(url_for('product_create', barcode=request.args.get('barcode'), next=request.url))

    InventoryItem(product=product,
                  best_before=datetime.now() + timedelta(days=product.best_before_days),
                  quantity = product.quantity).save()

    return redirect(url_for('inventoryitem_list'))

BARCODE_PLACEHOLDER = '{CODE}'
def scan_barcode(redirect_to):
    """Redirec to a barcode scanning application.

    Args:
        next: str, should have a BARCODE_PLACEHOLDER substring where the barcode should go and be
            externally-reachable.
    """
    return redirect('zxing://scan/?ret=' + redirect_to)

@app.route('/inventoryitem/remove/by_barcode')
def inventoryitem_remove_by_barcode():
    if 'barcode' not in request.args:
        return scan_barcode(redirect_to=url_for('inventoryitem_remove_by_barcode', barcode=BARCODE_PLACEHOLDER, _external=True))
    else:
        try:
            product = Product.objects.get(barcode=request.args['barcode'])
        except Product.DoesNotExist:
            return abort(404)

        items = InventoryItem.objects.filter(product=product.id).order_by('best_before')
        if not items:
            return abort(404)

        return redirect(url_for('inventoryitem_remove', id=items.first().id))

@app.route('/inventoryitem/<id>/remove', methods=['GET', 'POST'])
def inventoryitem_remove(id):
    class InventoryItemRemoveForm(Form):
        quantity = html5_fields.DecimalField()

    inventoryitem = InventoryItem.objects.get(id=id)

    form = InventoryItemRemoveForm()
    if form.validate_on_submit():
        inventoryitem.quantity = inventoryitem.quantity - form.quantity.data
        if inventoryitem.quantity <= 0:
            inventoryitem.delete()
        else:
            inventoryitem.save()
        return redirect(url_for('inventoryitem_list'))
    else:
        form.quantity.data = inventoryitem.quantity
        return render_template('inventoryitem_remove.html', inventoryitem=inventoryitem, form=form)


class ProductForm(RedirectForm):
    barcode = fields.TextField()
    name = fields.TextField()
    trading_unit = fields.TextField()
    category = fields.TextField()
    best_before_days = html5_fields.IntegerField()

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
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data,
                          best_before_days=form.best_before_days.data,
                          quantity=form.get_quantity(),
                          barcode=form.barcode.data)
        product.category, _ = ProductCategory.objects.get_or_create(name=form.category.data,
                                                                    unit=form.get_unit())
        product.save()

        return form.redirect('inventoryitem_list')
    else:
        if 'barcode' not in request.values:
            return scan_barcode(redirect_to=url_for('product_create', barcode=BARCODE_PLACEHOLDER, next=request.args.get('next'), _external=True))

        form.barcode.data = request.values['barcode']
        codecheck_product = codecheck.get_product_data_by_barcode(form.barcode.data)
        if codecheck_product:
            form.name.data = codecheck_product['name']
            form.trading_unit.data = str(codecheck_product['quantity']) + codecheck_product['unit']
            form.category.data = codecheck_product['category']
        return render_template('product_create.html', form=form)
