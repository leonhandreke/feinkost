import mongoengine

from feinkost import app, db

class Product(db.Document):
    gtin = db.StringField()
    name = db.StringField()
    quantity = db.StringField()
    best_before_days = db.IntField()

class InventoryItem(db.Document):
    product = db.ReferenceField(Product, reverse_delete_rule=mongoengine.DENY)
    best_before = db.DateTimeField()
    quantity = db.StringField()

