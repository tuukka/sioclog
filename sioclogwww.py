#!/usr/bin/env python

"""sioclogwww.py - a WWW interface for displaying logs

Example usage (in a CGI script): 
from sioclogwww import runcgi
runcgi("sioclogbot.log")
"""

import cgi, os

from channellog import OffFilter, ChannelFilter, TimeFilter, HtmlSink, TurtleSink, RawSink, ChannelsAndDaysSink, run
from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, DC, DCTERMS, XSD, FOAF, SIOC, SIOCT, DS
from users import render_user, render_user_index

def runcgi(logfile):
    HTTP_HOST = os.environ.get('HTTP_HOST', "")
    SERVER_PORT = os.environ.get('SERVER_PORT', "")
    REQUEST_URI = os.environ.get('REQUEST_URI', "")
    HTTP_ACCEPT = os.environ.get('HTTP_ACCEPT', "")
    PATH_INFO = os.environ.get('PATH_INFO', "")

#    query = cgi.FieldStorage()
#    channel = query.getfirst("channel", "")
#    timeprefix = query.getfirst("time", "")

    if REQUEST_URI.endswith(".html"):
        extension = ".html"
        format = "html"
    elif REQUEST_URI.endswith(".turtle"):
        extension = ".turtle"
        format = "turtle"
    elif REQUEST_URI.endswith(".txt"):
        extension = ".txt"
        format = "raw"
    else:
        # XXX do real content negotiation, e.g. mimeparse.py
        extension = ""
        if "turtle" in HTTP_ACCEPT:
            format = "turtle"
        elif "html" in HTTP_ACCEPT:
            format = "html"
        elif "text" in HTTP_ACCEPT:
            format = "raw"
        else:
            format = "turtle" # default

    parts = PATH_INFO.split('/')
    # remove extension if any:
    if parts[-1].endswith(extension):
        parts[-1] = parts[-1][:-len(extension) or None]

    if len(parts) > 1 and parts[1] not in ["channels", "users"]:
        parts.insert(1, "channels") # XXX default type for now

    if len(parts) > 1:
        restype = parts[1]
    else:
        restype = ""

    if len(parts) > 2:
        channel = parts[2]
    else:
        channel = ""

    if len(parts) > 3:
        timeprefix = parts[3]
    else:
        timeprefix = ""

    # XXX the following assumes http over port 80, no QUERY_STRING
    requesturi = "http://"+HTTP_HOST+REQUEST_URI
    datauri = requesturi
    # remove extension if any, to reset content negotiation in datauri:
    if datauri.endswith(extension):
        datauri = datauri[:-len(extension) or None]
        
    # FIXME can't infer this from CGI info?
    datarooturi = "http://irc.sioc-project.org/"

    if format == "html":
        print "Content-type: text/html; charset=utf-8"
        print
    elif format == "turtle":
        print "Content-type: application/x-turtle; charset=utf-8"
        print
    elif format == "raw":
        print "Content-type: text/plain; charset=utf-8"
        print

    if restype == "users" and channel:
        render_user(format, datarooturi, channel, datauri)
    elif restype == "users":
        # show user index
        render_user_index(format, datarooturi, datauri)
    elif channel and timeprefix:
        # show log
        if format == "html":
            sink = HtmlSink(datarooturi, channel, timeprefix, datauri)
        elif format == "turtle":
            sink = TurtleSink(datarooturi, channel, timeprefix)
        elif format == "raw":
            sink = RawSink()

        pipeline = OffFilter(ChannelFilter('#'+channel,
                                           TimeFilter(timeprefix, 
                                                      sink
                                                      )
                                           ))

        run(file(logfile), pipeline)

    else:
        # show index
        sink = ChannelsAndDaysSink()

        if channel:
            pipeline = ChannelFilter('#'+channel, sink)
        elif timeprefix:
            pipeline = TimeFilter(timeprefix, sink)
        else:
            pipeline = sink

        run(file(logfile), pipeline)

        if format == "html":
            html_index(sink, datarooturi, datauri, channel)
        elif format == "turtle":
            turtle_index(sink, datarooturi, datauri, channel)
        # XXX more formats

def turtle_index(sink, root, selfuri, querychannel):
    triples = []

    freenodeURI = root + "#freenode"

    triples += [(freenodeURI, RDFS.label, PlainLiteral("Freenode"))]

    channels = sorted(sink.channels.keys())
    channelURIs = []
    for channel in channels:
        channelID = channel.strip("#").lower()
        channelURI = root + channelID + "#channel"
        channelURIs.append(channelURI)

        oldChannelURI = "irc://freenode/%23" + channelID

        triples += [None,
                    (freenodeURI, SIOC.space_of, channelURI),
                    (channelURI, OWL.sameAs, oldChannelURI),
                    (channelURI, RDF.type, SIOC.Forum),
                    (channelURI, RDF.type, SIOCT.ChatChannel),
                    (channelURI, RDFS.label, 
                     PlainLiteral("#" + channel)),
                    ]
        
        for day in sorted(sink.channel2days[channel]):
            logURI = "%s%s/%s" % (root, channelID, day)
            triples += [(channelURI, RDFS.seeAlso, logURI)]

    writer = TurtleWriter(None, namespaces)
    if querychannel and channels:
        title = "Index of #%s" % channels[0]
        writer.write([("", FOAF.primaryTopic, channelURIs[0])])
    elif querychannel:
        title = "Empty index"
    else:
        title = "Index of some IRC discussion logs"
        writer.write([("", FOAF.primaryTopic, freenodeURI)])
        writer.write([("", FOAF.topic, channelURI)
                     for channelURI in channelURIs])
    writer.write([("", RDFS.label, PlainLiteral(title))])

    writer.setBase(root)
    writer.write(triples)
    writer.close()

def html_index(sink, root, selfuri, querychannel):

    channels = sorted(sink.channels.keys())

    if querychannel:
        title = "Channel #%s" % channels[0]
    else:
        title = "Some IRC discussion logs"

    print """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html 
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>%s</title>
<link rel="meta" href="http://triplr.org/rdf/%s" type="application/rdf+xml" title="SIOC"/>
<style type="text/css"><!--
div.logo-bar {
    float: right;
    text-align: center;

//    background: #CCCCFF;

    border-style: solid;
    border-color: #9999CC;
    border-width: 2px;
}
td { 
    vertical-align: top;
}
img {
    border: none;
    margin: 1em;
}
--></style>
</head>
<body>""" % (title, selfuri)

    if selfuri == root:
        selfuri2 = root + "index"
    else:
        selfuri2 = selfuri

    print "<h1>%s</h1>" % title
    print """<p>Available formats: <a href="%s">content-negotiated</a> <a href="%s.html">html</a> <a href="%s.turtle">turtle</a> (see <a href="http://sioc-project.org">SIOC</a> for the vocabulary) </p>""" % (selfuri, selfuri2, selfuri2)

    if querychannel:
        print """<p>This is a discussion channel on the Freenode IRC network.
</p>"""
    else:
        print """
<div class="logo-bar">
<a href="http://fenfire.org/"><img src="http://fenfire.org/logo.png" 
alt="Fenfire" title="The Fenfire project" /></a>
<br />
<a href="http://sioc-project.org/"><img src="http://sioc-project.org/files/sioc_button.gif" 
alt="SIOC" title="Semantically-Interlinked Online Communities" /></a>
<br />
<a href="http://linkeddata.org/"><img src="http://irc.sioc-project.org/images/linkingopendata.png"
width="100" alt="Linked Data" title="Linked Data" /></a>
<br />
<a href="http://www.w3.org/RDF/"><img src="http://www.w3.org/RDF/icons/rdf_w3c_icon.96"
alt="RDF" title="RDF Resource Description Framework" /></a>
</div>

<p>The URIs of unspecified format are content-negotiated and can thus be 
opened equally well in web browsers and in RDF browsers such 
as <a href="http://fenfire.org/">Fenfire</a>. The RDF data uses the 
SIOC vocabulary (see the <a href="http://sioc-project.org/">
Semantically-Interlinked Online Communities Project</a> for details).</p>
""" 

    print """
<p><strong>Privacy notice:</strong> In line with Freenode policy, it is 
possible to exclude your lines from these logs. Based on a common convention, 
you can achieve this by prepending <code>[off]</code> to your messages and 
actions.
</p>
<!-- Google CSE Search Box Begins  -->
<form action="http://www.google.com/cse" id="searchbox_009180828701492049973:6ly
79qxejks">
  <p>
  <input type="hidden" name="cx" value="009180828701492049973:6ly79qxejks" />
  <input type="text" name="q" size="25" />
  <input type="submit" name="sa" value="Search" />
  </p>
</form>
<!-- <script type="text/javascript" src="http://www.google.com/coop/cse/brand?fo
rm=searchbox_009180828701492049973%3A6ly79qxejks&lang=en"></script> -->
<!-- Google CSE Search Box Ends -->"""

    if not querychannel:
        print """<h2>Channels</h2>"""
        print """<p><em>See also <a href="%s">users</a>.</p>""" % (root + "users")
    else:
        print """<h2>Daily logs</h2>"""

    print "<table>"
    print "<thead><tr><th></th>"
    for channel in channels:
        channelID = channel.strip("#").lower()
        channelURI = root + channelID + "#channel"
        print """<th><a href="%s">#%s</a></th>""" % (channelURI, channel)
    print "</tr></thead><tbody>"            
    for day in reversed(sorted(sink.days.keys())):
        print "<tr>"
        print "<th>%s</th>" % day
        for channel in sorted(sink.channels.keys()):
            print "<td>"
            if channel in sink.day2channels[day]:
                print '<a href="/%s/%s">#%s</a>' % (channel, day, channel)
            print "</td>"
        print "</tr>"
    print """</tbody></table>
<p>Older logs are still at <a href="http://tuukka.iki.fi/tmp/logindex">http://tuukka.iki.fi/tmp/logindex</a>.
Hopefully they'll be merged here soon.</p>

<p>Rendered by <a href="http://github.com/tuukka/sioclog/blob/master/sioclogwww.py">sioclogwww.py</a>.</p>
</body>
</html>"""
