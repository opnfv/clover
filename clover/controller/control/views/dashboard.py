# Copyright (c) Authors of Clover
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0

from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

simple_page = Blueprint('simple_page', __name__)


@simple_page.route('/dashboard', defaults={'page': 'index'})
def show(page):
    try:
        return render_template('home.html')
    except TemplateNotFound:
        abort(404)
