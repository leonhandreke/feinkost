from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.bootstrap import Bootstrap

import settings

app = Flask(__name__)
app.config.from_object(settings)

Bootstrap(app)

db = MongoEngine(app)

from feinkost import views, models
