# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request
import redis

file_upload = Blueprint('file_upload', __name__)

HOST_IP = 'redis'


@file_upload.route("/upload", methods=['GET', 'POST'])
def upload_meta():
    try:
        content = request.form
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        response = content.get('upload.name')
        r.set('upload_meta', response)
    except Exception as e:
        response = e
        r.set('upload_meta', "failure")
    return response
