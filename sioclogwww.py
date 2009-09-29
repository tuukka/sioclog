#!/usr/bin/env python

"""sioclogwww.py - a WWW interface for displaying logs

Example usage (in a CGI script): 
from sioclogwww import runcgi
runcgi("sioclogbot.log")
"""

import cgi, os

from ircbase import w3c_timestamp, convert_timestamp_to_z

from channellog import OffFilter, ChannelFilter, TimeFilter, HtmlSink, TurtleSink, RawSink, ChannelsAndDaysSink, run, AddLinksFilter, BackLogHtmlSink, ChannelMessageTailFilter, UserFilter, EventSink
from templating import new_context, get_template, expand_template
from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, DC, DCTERMS, XSD, FOAF, SIOC, SIOCT, DS
from users import render_user, render_user_index, get_nick2people
from styles import css_stylesheet

def runcgi(datarooturi, logfiles):

    HTTP_HOST = os.environ.get('HTTP_HOST', "")
    SERVER_PORT = os.environ.get('SERVER_PORT', "")
    REQUEST_URI = os.environ.get('REQUEST_URI', "")
    HTTP_ACCEPT = os.environ.get('HTTP_ACCEPT', "")
    PATH_INFO = os.environ.get('PATH_INFO', "")

    query = cgi.FieldStorage()
    up_to = query.getfirst("up_to", None)
#    channel = query.getfirst("channel", "")
#    timeprefix = query.getfirst("time", "")

    if PATH_INFO == "/styles.css":
        print "Content-type: text/css"
        print
        css_stylesheet()
        return
    elif PATH_INFO == "/sitemap.xml":
        print "Content-type: text/xml"
        sink = ChannelsAndDaysSink()
        run(logfiles, sink)
        sitemap_index(sink, datarooturi)
        return

    if REQUEST_URI.endswith(".html"):
        extension = ".html"
        format = "html"
    elif REQUEST_URI.endswith(".turtle"):
        extension = ".turtle"
        format = "turtle"
    elif REQUEST_URI.endswith(".ttl"):
        extension = ".ttl"
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
            if "Googlebot" in os.environ.get('HTTP_USER_AGENT', ""):
                format = "html" # Accept: */* isn't the full truth...
            else:
                format = "turtle" # default

    parts = PATH_INFO.split('/')
    # remove extension if any:
    if parts[-1].endswith(extension):
        parts[-1] = parts[-1][:-len(extension) or None]

    if len(parts) > 1 and parts[1] not in ["channels", "users", "backlog"]:
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
    datauri = requesturi.split("?")[0] # exclude QUERY_STRING
    # remove extension if any, to reset content negotiation in datauri:
    if datauri.endswith(extension):
        datauri = datauri[:-len(extension) or None]
        
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
        sink = ChannelsAndDaysSink()
        run(logfiles, sink)

        latestsink = EventSink(datarooturi, None, None, datauri)
        latestpipeline = OffFilter(UserFilter(channel, ChannelMessageTailFilter(1, AddLinksFilter(latestsink))))
        run(logfiles, latestpipeline)

        render_user(sink, format, crumbs, datarooturi, channel, datauri, latestsink)
    elif restype == "users":
        sink = ChannelsAndDaysSink()
        run(logfiles, sink)
        render_user_index(sink, format, crumbs, datarooturi, datauri)
    elif channel and timeprefix:
        # show log
        if format == "html":
            if restype == "backlog":
                # FIXME temporary hack to get the params right:
                nick = channel
                channel = timeprefix
                timeprefix = nick
                sink = AddLinksFilter(BackLogHtmlSink(nick, up_to, crumbs, datarooturi, channel, timeprefix, datauri))
                timeprefix = ""
            else:
                sink = AddLinksFilter(HtmlSink(crumbs, datarooturi, channel, timeprefix, datauri))
        elif format == "turtle":
            sink = AddLinksFilter(TurtleSink(datarooturi, channel, timeprefix))
        elif format == "raw":
            sink = RawSink()

        pipeline = OffFilter(ChannelFilter('#'+channel,
                                           TimeFilter(timeprefix, 
                                                      sink
                                                      )
                                           ))

        run(logfiles, pipeline)

    else:
        # show index
        sink = ChannelsAndDaysSink()

        if channel:
            pipeline = ChannelFilter('#'+channel, sink)
        elif timeprefix:
            pipeline = TimeFilter(timeprefix, sink)
        else:
            pipeline = sink

        run(logfiles, pipeline)

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

    if querychannel:
        nicks = sorted(sink.channel2nicks[querychannel].keys())
        for nick in nicks:
            userURI = root + "users/%s#user" % nick
            triples += [None,
                        (channelURI, SIOC.has_subscriber, userURI),
                        (userURI, RDFS.label, PlainLiteral(nick)),
                        ]

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

    if querychannel:
        nicks = sorted(sink.channel2nicks[querychannel].keys())
    else:
        nicks = sorted(sink.nicks)

    userdata = []
    for nick in nicks:
        userURI = root + "users/%s#user" % nick
        userdata.append({'uri': userURI, 'name': nick})
    context.addGlobal('users', userdata)
    context.addGlobal('nick2people', get_nick2people())

    template = get_template('index')
    expand_template(template, context)

def sitemap_entry(uri, timestamp, frequency, priority):
    print "<url>"
    print "  <loc>%s</loc>""" % uri
    if timestamp:
        print "  <lastmod>%s</lastmod>" % timestamp
    if frequency:
        print "  <changefreq>%s</changefreq>" % frequency
    if priority:
        print "  <priority>%s</priority>" % priority
    print "</url>"

def sitemap_index(sink, root):
    now = convert_timestamp_to_z(w3c_timestamp())
    today = now.split("T")[0]
    print """
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""

    # individual files:
    sitemap_entry(root, max(sink.channel2latest.values()), "hourly", 1.0)
    sitemap_entry(root+"about", None, "weekly", 1.0)
    sitemap_entry(root+"users", None, "daily", 1.0)
    print
    # users:
    nicks = sorted(sink.nicks.keys())
    for nick in nicks:
        sitemap_entry(root+"users/"+nick, sink.nick2latest[nick], "weekly", 0.9)
    print
    # channels:
    channels = sorted(sink.channels.keys())
    channelURIs = []
    for channel in channels:
        channelID = channel.strip("#").lower()
        channelURI = root + channelID + "#channel"

        sitemap_entry(channelURI, sink.channel2latest[channelID], "hourly", 0.9)
    print
    # today's logs:
    for channel in channels:
        channelID = channel.strip("#").lower()
        logURI = "%s%s/%s" % (root, channelID, today)
        latest = max([today, sink.channel2latest[channelID]])
        sitemap_entry(logURI, latest, "hourly", 0.9)
    print
    # daily logs:
    for channel in channels:
        channelID = channel.strip("#").lower()
        for day in sorted(sink.channel2days[channel]):
            logURI = "%s%s/%s" % (root, channelID, day)

            if day != today:
                sitemap_entry(logURI, day, "never", 0.8)

    print "</urlset>"

if __name__ == '__main__':
    import sys, logging
    simpleTALLogger = logging.getLogger("simpleTAL")
    simpleTALLogger.setLevel(logging.DEBUG)
    runcgi(sys.argv[1])
