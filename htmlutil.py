#!/usr/bin/env python

"""htmlutil.py - a module for dealing with HTML

Example usage: 
from htmlutil import html_escape, html_escapes
print '<a href="%s">%s</a>' % html_escapes(uri, label)
"""

def html_escape(s):
    s = "%s" % s
    # & needs to be escaped first, before more are introduced:
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s

def html_escapes(*args):
    return tuple(map(html_escape, args))
