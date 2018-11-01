# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Flask
from api.collector import collector
from views.visibility import visibility
from api.visibility import visibility_api
from api.snort import snort
from api.halyard import halyard
from api.nginx import nginx
from api.jmeter import jmeter
from api.file_upload import file_upload
import logging

logging.basicConfig(filename='flask.log', level=logging.DEBUG)

application = Flask(__name__)

try:
    # Register blueprints
    application.register_blueprint(collector)
    application.register_blueprint(visibility)
    application.register_blueprint(visibility_api)
    application.register_blueprint(snort)
    application.register_blueprint(halyard)
    application.register_blueprint(nginx)
    application.register_blueprint(jmeter)
    application.register_blueprint(file_upload)
except Exception as e:
    logging.debug(e)


@application.route("/test")
def test():
    return "<h1 style='color:blue'>clover-controller up</h1>"


if __name__ == "__main__":
    application.run(host='0.0.0.0')
