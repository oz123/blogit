#!/usr/bin/env python
"""
    A simple application that shows how Bottle and jQuery get along.

    :copyright: (c) 2015 by Oz Nahum Tiram.
    :license: BSD, see LICENSE for more details.

    Inspired by the same example given in Flask
    :copyright: (c) 2015 by Armin Ronacher.
"""
from bottle import route, run, debug, template, request
import json


@route('/_add_numbers')
def add_numbers():
    """Add two numbers server side, ridiculous but well..."""
    a = request.params.get('a', 0, type=int)
    b = request.params.get('b', 0, type=int)
    return json.dumps({'result': a+b})


@route('/foo/:no')
def bar(no):
    return template('index.tpl', request=request)


@route('/')
def index():
    return template('index.tpl', request=request)


debug(True)
run(port=9030)
