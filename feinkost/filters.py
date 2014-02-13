import decimal

from feinkost import app

UNIT_CONVERSIONS = {
    ('ml', 'l'): lambda x: x / 1000,
    ('l', 'ml'): lambda x: x * 1000,
    ('g', 'kg'): lambda x: x / 1000,
    ('kg', 'g'): lambda x: x * 1000
}

@app.template_filter('render_quantity')
def render_quantity_filter(q):
    quantity, unit = q

    if not unit:
        return str(quantity)

    new_unit = unit
    if unit == 'l' and quantity < 1:
        new_unit = 'ml'
    if unit == 'ml' and quantity > 1000:
        new_unit = 'l'
    if unit == 'kg' and quantity < 1:
        new_unit = 'g'
    if unit == 'g' and quantity > 1000:
        new_unit = 'kg'

    if new_unit != unit:
        new_quantity = UNIT_CONVERSIONS.get((unit, new_unit))(quantity)
    else:
        new_quantity = quantity

    return str(new_quantity.quantize(decimal.Decimal('1.'), rounding=decimal.ROUND_DOWN)) + new_unit
