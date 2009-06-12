#!/usr/bin/env python

"""sioclog.cgi - a CGI script for running the WWW interface on a HTTP server
"""

import sys
# change this to point to the location of sioclogwww.py etc.:
sys.path.insert(0, '/home/sioclog/sioclog')

from sioclogwww import runcgi

# change this to point to the log written by sioclogbot.py
runcgi("/home/sioclog/freenode.log")
