import mongoengine

from feinkost import app, db, constants


class ProductCategory(db.Document):
    name = db.StringField(required=True, unique=True)
    unit = db.StringField(
        choices=[
            constants.UNIT_GRAM,
            constants.UNIT_LITER,
            constants.UNIT_NONE])
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
    # Barcode of the product. Made unique by an index
    barcode = db.StringField()
    name = db.StringField()
    # Quantity that is sold in the store
    quantity = db.DecimalField(required=True)
    best_before_days = db.IntField()
    category = db.ReferenceField(ProductCategory, reverse_delete_rule=mongoengine.DENY, required=True)

    meta = {
        'indexes': [
            # Ensure barcodes may be empty, but if set, be unique
            { 'fields': ['barcode'], 'sparse': True, 'unique': True }
        ]
    }

    def get_unit(self):
        return self.category.get_unit()

class InventoryItem(db.Document):
    product = db.ReferenceField(Product, reverse_delete_rule=mongoengine.DENY, required=True)
    best_before = db.DateTimeField()
    quantity = db.DecimalField(required=True)

    def get_unit(self):
      return self.product.get_unit()
