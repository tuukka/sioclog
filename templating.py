#!/usr/bin/env python

"""templating.py - a module for rendering html with templates

Example usage:
from templating import new_context, get_template, expand_template
context = new_context()
context.addGlobal('datarooturi', datarooturi)
context.addGlobal('datauri', datauri)
template = get_template('users')
expand_template(template, context)
"""

from __future__ import with_statement

import sys, os

from simpletal import simpleTAL, simpleTALES

def new_context():
    return simpleTALES.Context()

def get_template(name):
    dirpath = os.path.dirname(__file__)
    with file(os.path.join(dirpath, "%s.html" % name)) as templateFile:
        return simpleTAL.compileXMLTemplate(templateFile.read())

def expand_template(template, context):
    template.expand(context, sys.stdout, "UTF-8")
    
if __name__ == '__main__':
    context = new_context()
    context.addGlobal("datauri", "http://datauri")
    context.addGlobal("title", "Hello World")

    template = get_template("users")

    context.addGlobal("users", [{'nick': 'foo', 'uri': 'bar'},
                                {'nick': 'foo2', 'uri': 'bar2'}])
    expand_template(template, context)

