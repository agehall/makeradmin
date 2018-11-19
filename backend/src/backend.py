from flask import Flask
from flask_uploads import UploadSet, IMAGES, configure_uploads

import member
import statistics
import webshop
from service import format_datetime


app = Flask(__name__)
app.jinja_env.filters['format_datetime'] = format_datetime
app.register_blueprint(webshop.instance.blueprint)
app.register_blueprint(statistics.instance.blueprint)
app.register_blueprint(member.instance.blueprint)


# Configure upload directory for images
product_images = UploadSet('productimages', IMAGES)
# This is a horrible way to configure paths, but oh well...
app.config['UPLOADED_PRODUCTIMAGES_DEST'] = 'static/product_images'
configure_uploads(app, product_images)