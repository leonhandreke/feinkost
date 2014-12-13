from decimal import Decimal
from enum import Enum

import mongoengine

from feinkost import app, db, constants
from feinkost.fields import EnumField


class ProductCategory(db.Document):
    name = db.StringField(required=True, unique=True)
    unit = db.StringField(
        choices=constants.DATABASE_UNITS)
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

    def get_inventory_quantity(self):
        quantity = Decimal(0)
        for p in Product.objects.filter(category=self):
            quantity += p.get_inventory_quantity()
        for i in InventoryItem.objects.filter(category=self):
            quantity += i.capacity * i.quantity
        return quantity


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

    def get_inventory_quantity(self):
        q = Decimal(0)
        for i in  InventoryItem.objects.filter(product=self):
            q += self.quantity * i.quantity
        return q


class InventoryItem(db.Document):

    # For direct updating of inventory items, such as refillable containers
    barcode = db.StringField()

    # For refillable containers
    capacity = db.DecimalField()
    category = db.ReferenceField('ProductCategory', reverse_delete_rule=mongoengine.DENY)

    product = db.ReferenceField('Product', reverse_delete_rule=mongoengine.DENY)
    best_before = db.DateTimeField()

    # Stored as a fraction of the quantity of the product or the capacity of the container
    quantity = db.DecimalField()

    class QuantityState(Enum):
        EMPTY = 0
        ALMOST_EMPTY = 1
        PARTIALLY_FULL = 2
        FULL = 3

        @property
        def display_name(self):
            return {
                self.__class__.EMPTY: "Empty",
                self.__class__.ALMOST_EMPTY: "Almost Empty",
                self.__class__.PARTIALLY_FULL: "Partially Full",
                self.__class__.FULL: "Full"
            }[self]

    quantity_state = EnumField(QuantityState)

    meta = {
        'indexes': [
            # Ensure barcodes may be empty, but if set, be unique
            {'fields': ['barcode'], 'sparse': True, 'unique': True}
        ]
    }

    def get_display_name(self):
        if self.product:
            return self.product.name
        else:
            return self.category.name

    def get_category(self):
        return getattr(self, 'category', None) or self.product.category

    def get_unit(self):
        if self.product:
            return self.product.get_unit()
        else:
            return self.category.get_unit()

    def is_refillable_container(self):
        return self.capacity is not None
