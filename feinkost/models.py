import mongoengine

from feinkost import app, db


class ProductCategory(db.Document):
    name = db.StringField(required=True, unique=True)
    unit = db.StringField()
    category = db.ReferenceField('ProductCategory', reverse_delete_rule=mongoengine.DENY)

    def get_unit(self):
        """
        Returns:
            str, the unit of measurement that this product category should be counted in.
        """
        current_category = self
        while not current_category.unit and current_category.category:
            current_category = current_category.category
        return current_category.unit


class Product(db.Document):
    barcode = db.StringField(unique=True)
    name = db.StringField()
    # Quantity that is sold in the store
    quantity = db.DecimalField(required=True)
    best_before_days = db.IntField()
    category = db.ReferenceField(ProductCategory, reverse_delete_rule=mongoengine.DENY, required=True)


class InventoryItem(db.Document):
    category = db.ReferenceField(ProductCategory, reverse_delete_rule=mongoengine.DENY, required=True)
    best_before = db.DateTimeField()
    quantity = db.DecimalField(required=True)

    def get_unit(self):
      return self.category.get_unit()
