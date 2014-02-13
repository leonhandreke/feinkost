import decimal

from flask import render_template

from feinkost import app
from feinkost.models import InventoryItem

@app.route('/')
def inventoryitem_list():
    items = []
    for item in InventoryItem.objects:
        items.append({
            'title': item.product.name,
            'quantity': item.quantity,
            'unit': item.get_unit(),
            'best_before': item.best_before
            })

    return render_template('inventoryitem_list.html', inventory_items=items)
