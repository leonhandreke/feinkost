from feinkost.models import Product, InventoryItem, ProductCategory

for c in Product, InventoryItem, ProductCategory:
    c.drop_collection()
