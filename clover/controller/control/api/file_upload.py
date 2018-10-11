# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, request, Response, jsonify
import redis
import logging

file_upload = Blueprint('file_upload', __name__)

HOST_IP = 'redis.default'


@file_upload.route("/upload", methods=['GET', 'POST'])
def set_upload_metadata():
    try:
        response = "Uploaded file(s) successfully"
        content = request.form
        logging.debug(content)
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        # Try various variable names
        upload_var_names = ['upload', 'file1', 'file2', 'file3',
                            'file4', 'file5', 'file6']
        for n in upload_var_names:
            try:
                param_name = n + '.name'
                meta_name = content.get(param_name)
                if meta_name:
                    param_path = n + '.path'
                    param_server = n + '.server'
                    meta_path = content.get(param_path)
                    meta_server = content.get(param_server)
                    entry = meta_name + ':' + meta_path + ':' + meta_server
                    r.sadd('upload_metadata', entry)
            except Exception as e:
                print("no metadata")
    except Exception as e:
        logging.debug(e)
        return Response('Unable to write file metadata to redis', status=400)
    return response


@file_upload.route("/upload/get", methods=['GET', 'POST'])
def get_upload_metadata():
    try:
        r = redis.StrictRedis(host=HOST_IP, port=6379, db=0)
        response = jsonify(list(r.smembers('upload_metadata')))
    except Exception as e:
        logging.debug(e)
        return Response('Unable to retrieve upload metadata', status=400)
    return response
