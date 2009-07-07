#!/usr/bin/env python

"""htmlutil.py - a module for dealing with html data

Example usage: 
XXX
"""

def escape_html(s):
    s = str(s)
    # & needs to be escaped first, before more are introduced:
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s

def escape_htmls(*args):
    return tuple(map(escape_html, args))
