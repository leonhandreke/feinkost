from datetime import date

from feinkost.models import Product, InventoryItem, ProductCategory
from feinkost.constants import *

for c in Product, InventoryItem, ProductCategory:
    c.drop_collection()

milch = ProductCategory(name='Milch', unit=UNIT_LITER).save()
mandeln = ProductCategory(name='Mandeln', unit=UNIT_GRAMM).save()
eisbergsalat = ProductCategory(name='Eisbergsalat').save()

aldi_mandeln = Product(barcode='1', name='Sweet Valley Kalifornische Mandeln, ganz', quantity=200, category=mandeln, best_before_days=365).save()
aldi_bio_milch = Product(barcode='2', name='ALDI Bio-Milch', quantity=1, category=milch, best_before_days=10).save()
schwarzwaldmilch = Product(barcode='3', name='Schwarzwaldmilch Bio-Milch', quantity=1, category=milch, best_before_days=8).save()
aldi_eisbergsalat = Product(name='Eisbergsalat', quantity=1, category=eisbergsalat, best_before_days=3).save()

InventoryItem(product=aldi_mandeln, quantity=200, best_before=date(2015, 8, 31)).save()
InventoryItem(product=aldi_bio_milch, quantity=1, best_before=date(2014, 11, 28)).save()
InventoryItem(product=aldi_eisbergsalat, quantity=0.5, best_before=date(2014, 11, 11)).save()
