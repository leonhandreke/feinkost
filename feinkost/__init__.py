from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap
from flask.ext.mobility import Mobility

import settings

app = Flask(__name__)
app.config.from_object(settings)

Bootstrap(app)
Mobility(app)

db = MongoEngine(app)

from feinkost import filters, views, models
