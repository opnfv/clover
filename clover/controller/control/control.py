# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Flask, request, jsonify
from views.dashboard import simple_page
from api.collector import collector
from api.snort import snort
from api.file_upload import file_upload
import logging

application = Flask(__name__)

# Register blueprints
application.register_blueprint(simple_page)
application.register_blueprint(collector)
application.register_blueprint(snort)
application.register_blueprint(file_upload)

logging.basicConfig(filename='flask.log', level=logging.DEBUG)


@application.route("/")
def test():
    return "<h1 style='color:blue'>clover-controller up</h1>"


@application.route("/config_server/<server>")
def show_server(server):
    return "User %s" % server


@application.route("/get_json", methods=['GET', 'POST'])
def get_json():
    try:
        content = request.json
        cmd = content["cmd"]
        resp = jsonify({"cmd": cmd})
    except Exception as e:
        resp = e
    return resp


if __name__ == "__main__":
    application.run(host='0.0.0.0')
