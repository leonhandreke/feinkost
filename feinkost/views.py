import decimal
from datetime import datetime, timedelta
import re
import urllib.parse

from flask import render_template, request, redirect, url_for, abort

from wtforms import fields
from wtforms.validators import ValidationError
from flask.ext.mongoengine.wtf import model_form
from flask.ext.wtf import Form
from flask.ext.wtf import html5 as html5_fields

from feinkost import app
from feinkost import codecheck
from feinkost.forms import RedirectForm, ProductCategoryField, QuantityUnitField
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


class ProductForm(Form):
    barcode = fields.TextField()
    name = fields.TextField()
    trading_unit = QuantityUnitField()
    category = ProductCategoryField()
    best_before_days = html5_fields.IntegerField()

    TRADING_UNIT_RE = '(\d+\.?\d*)(\w*)'

    def validate_trading_unit(self, field):
        unit = field.get_trading_unit()[1]
        product_category = ProductCategory.objects.filter(id=self.category.data).first()
        if product_category and not product_category.get_unit() == unit:
            raise ValidationError("Unit does not match product category's unit.")

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
        if request.MOBILE and 'barcode' not in request.values:
            return scan_barcode(redirect_to=url_for('product_create', barcode=BARCODE_PLACEHOLDER, next=request.args.get('next'), _external=True))

        # Load barcode from request.values because the barcode scanner passes it as a GET variable
        form.barcode.data = request.values.get('barcode')
        if form.barcode.data:
            try:
                codecheck_product = codecheck.get_product_data_by_barcode(form.barcode.data)
            except:
                # TODO: More fine-grained exception handling, report errors with flash()
                codecheck_product = None

            if codecheck_product:
                form.name.data = codecheck_product['name']
                form.trading_unit.data = str(codecheck_product['quantity']) + codecheck_product['unit']
                form.category.data = codecheck_product['category']
        return render_template('product_edit.html', form=form)

@app.route('/product')
def product_list():
    # TODO: Order by category name (or even aggregate somehow?)
    return render_template('product_list.html', products=Product.objects, abs=abs, int=int)

@app.route('/product/<id>/edit', methods=['GET', 'POST'])
def product_edit(id):
    try:
        product = Product.objects.get(id=id)
    except Product.DoesNotExist:
        return abort(404)

    form = ProductForm(obj=product)
    if request.method == 'GET':
        form.trading_unit.data = str(product.quantity) + product.get_unit()

    if form.validate_on_submit():
        form.populate_obj(product)
        product.quantity = form.trading_unit.get_trading_unit()[0]
        product.save()
        return redirect(url_for('product_list'))
    else:
        return render_template('product_edit.html', product=product, form=form)
