#!/usr/bin/env python

"""sioclogwww.py - a WWW interface for displaying logs

Example usage (in a CGI script): 
from sioclogwww import runcgi
runcgi("sioclogbot.log")
"""

import cgi, os

from channellog import OffFilter, ChannelFilter, TimeFilter, HtmlSink, TurtleSink, RawSink, ChannelsAndDaysSink, run
from templating import new_context, get_template, expand_template
from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, DC, DCTERMS, XSD, FOAF, SIOC, SIOCT, DS
from users import render_user, render_user_index
from styles import css_stylesheet

def runcgi(logfile):
    HTTP_HOST = os.environ.get('HTTP_HOST', "")
    SERVER_PORT = os.environ.get('SERVER_PORT', "")
    REQUEST_URI = os.environ.get('REQUEST_URI', "")
    HTTP_ACCEPT = os.environ.get('HTTP_ACCEPT', "")
    PATH_INFO = os.environ.get('PATH_INFO', "")

#    query = cgi.FieldStorage()
#    channel = query.getfirst("channel", "")
#    timeprefix = query.getfirst("time", "")

    if PATH_INFO == "/styles.css":
        print "Content-type: text/css"
        print
        css_stylesheet()
        return

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

    crumbs = list(create_index_crumbs(datarooturi, datauri, restype, channel, 
                                      timeprefix))

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
        render_user(format, crumbs, datarooturi, channel, datauri)
    elif restype == "users":
        # show user index
        render_user_index(format, crumbs, datarooturi, datauri)
    elif channel and timeprefix:
        # show log
        if format == "html":
            sink = HtmlSink(crumbs, datarooturi, channel, timeprefix, datauri)
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
            html_index(sink, crumbs, datarooturi, datauri, channel)
        elif format == "turtle":
            turtle_index(sink, datarooturi, datauri, channel)
        # XXX more formats

def turtle_index(sink, root, datauri, querychannel):
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

def hash(**kwargs):
    return kwargs

def create_index_crumbs(root, datauri, restype, channel, timeprefix):
    yield hash(uri=root, label="Front page")

    if datauri == root:
        return
        
    if not restype:
        return

    yield hash(uri="%s%s" % (root, restype), label=restype)

    if not channel:
        return

    yield hash(uri="%s%s/%s" % (root, restype, channel), label=channel)

    if not timeprefix:
        return

    yield hash(uri="%s%s/%s/%s" % (root, restype, channel, timeprefix),
               label=timeprefix)

def html_index(sink, crumbs, root, datauri, querychannel):
    context = new_context()
    context.addGlobal('crumbs', crumbs)
    context.addGlobal('datarooturi', root)
    context.addGlobal('datauri', datauri)

    context.addGlobal('querychannel', querychannel)

    channels = sorted(sink.channels.keys())

    if querychannel:
        title = "Channel #%s" % channels[0]
    else:
        title = "Some IRC discussion logs"

    context.addGlobal('title', title)

    if datauri == root:
        datauri2 = root + "index"
    else:
        datauri2 = datauri

    context.addGlobal('datauri2', datauri2)

    channeldata = []
    for channel in channels:
        channelID = channel.strip("#").lower()
        channelURI = root + channelID + "#channel"
        channeldata.append({'uri': channelURI, 'name': channelID})

    # XXX list works around a bug in simpletal
    days = list(reversed(sorted(sink.days.keys())))

    context.addGlobal('channels', channeldata)
    context.addGlobal('days', days)
    context.addGlobal('day2channels', sink.day2channels)

    template = get_template('index')
    expand_template(template, context)


if __name__ == '__main__':
    import sys, logging
    simpleTALLogger = logging.getLogger("simpleTAL")
    simpleTALLogger.setLevel(logging.DEBUG)
    runcgi(sys.argv[1])
