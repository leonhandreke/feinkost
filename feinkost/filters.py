import decimal
from datetime import datetime

from flask import render_template

from feinkost.constants import *
from feinkost import models
from feinkost import app

# https://stackoverflow.com/questions/11227620/drop-trailing-zeros-from-decimal
def normalize_fraction(d):
    normalized = d.normalize()
    sign, digit, exponent = normalized.as_tuple()
    return normalized if exponent <= 0 else normalized.quantize(1)

@app.template_filter('render_inventory_item_quantity')
def render_inventory_item_quantity(inventory_item):
    # Check if it is a refillable container
    capacity = inventory_item.capacity or inventory_item.product.quantity
    quantity = capacity * inventory_item.quantity
    quantity, unit = get_display_quantity(quantity, inventory_item.get_unit())
    capacity, unit = get_display_quantity(capacity, inventory_item.get_unit())

    return render_template('filters/render_inventoryitem_quantity.html',
                           inventory_item=inventory_item,
                           QuantityState=models.InventoryItem.QuantityState,
                           capacity=capacity,
                           quantity=quantity,
                           unit=unit)

@app.template_filter('render_product_quantity')
def render_product_quantity(product):
    return ''.join(get_display_quantity(product.quantity, product.get_unit()))

def get_display_quantity(quantity, unit):
    if not unit:
        return str(normalize_fraction(quantity))

    new_unit = unit
    if unit == UNIT_LITER and quantity < 1:
        new_unit = UNIT_MILLILITER
    if unit == UNIT_GRAM and quantity > 1000:
        new_unit = UNIT_KILOGRAM

    if new_unit != unit:
        new_quantity = UNIT_CONVERSIONS.get((unit, new_unit))(quantity)
    else:
        new_quantity = quantity

    return (new_quantity.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_DOWN), new_unit)

@app.template_filter('timedelta_days')
def timedelta_days_filter(d):
    return (d - datetime.now()).days
