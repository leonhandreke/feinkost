import decimal
from datetime import datetime

from feinkost.constants import *
from feinkost import app

@app.template_filter('render_inventory_item_quantity')
def render_inventoryitem_quantity(inventory_item):
    # Check if it is a refillable container
    if inventory_item.capacity is not None:
        quantity = inventory_item.quantity * inventory_item.capacity
    else:
        quantity = inventory_item.quantity * inventory_item.product.quantity
    return render_quantity(quantity, inventory_item.get_unit())

@app.template_filter('render_product_quantity')
def render_product_quantity(product):
    return render_quantity(product.quantity, product.get_unit())

def render_quantity(quantity, unit):
    """Render a human-readable, possibly converted representation of the quantity and unit."""

    # https://stackoverflow.com/questions/11227620/drop-trailing-zeros-from-decimal
    def normalize_fraction(d):
        normalized = d.normalize()
        sign, digit, exponent = normalized.as_tuple()
        return normalized if exponent <= 0 else normalized.quantize(1)

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

    return str(new_quantity.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_DOWN)) + new_unit

@app.template_filter('timedelta_days')
def timedelta_days_filter(d):
    return (d - datetime.now()).days
