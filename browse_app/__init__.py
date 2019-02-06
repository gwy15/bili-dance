import flask
from flask_bootstrap import Bootstrap
import requests
import models

def getApp():
    app = flask.Flask(__name__)
    app.config.from_pyfile('config.py')

    Bootstrap().init_app(app)

    return app

app = getApp()

from browse_app import views
