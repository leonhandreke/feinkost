import decimal
from datetime import datetime

from feinkost.constants import *
from feinkost import app

@app.template_filter('render_quantity')
def render_quantity_filter(i):
    quantity = i.quantity * i.product.quantity
    unit = i.get_unit()

    if not unit:
        return str(quantity)

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
