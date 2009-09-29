#!/usr/bin/env python

"""sioclog.cgi - a CGI script for running the WWW interface on a HTTP server
"""

import sys

# change this to point to the location of sioclogwww.py etc.:
sys.path.insert(0, '/home/sioclog/sioclog')

from sioclogwww import runcgi

# change this to point to the logs written by sioclogbot.py, oldest first:
logfiles = ["/home/sioclog/freenode.log.2008", "/home/sioclog/freenode.log"]

# change this to point to the root URI where this installation is on the Web:
# FIXME can't infer this from CGI info?
rootURI = "http://irc.sioc-project.org/"

runcgi(rootURI, logfiles)
