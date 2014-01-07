import mongoengine

from flask import Flask, g, render_template
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap

import settings

app = Flask(__name__)
app.config.from_object(settings)

Bootstrap(app)

db = MongoEngine(app)

class Product(db.Document):
    gtin = db.StringField()
    name = db.StringField()
    quantity = db.StringField()
    best_before_days = db.IntField()

class InventoryItem(db.Document):
    product = db.ReferenceField(Product, reverse_delete_rule=mongoengine.DENY)
    best_before = db.DateTimeField()
    quantity = db.StringField()


@app.route('/')
def inventoryitem_list():
    return render_template('inventoryitem_list.html')


if __name__ == '__main__':
        app.run()
