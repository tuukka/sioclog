#!/usr/bin/env python

"""channellog.py - a module for filtering and rendering streams of IRC data

Example usage:
from channellog import OffFilter, ChannelFilter, TimeFilter, HtmlSink, TurtleSink, RawSink, ChannelsAndDaysSink, run
pipeline = ChannelFilter("#sioc", RawSink())
run(file("sioc.log"), pipeline)
"""

from traceback import print_exc

import ircbase
ircbase.dbg = False
from ircbase import parseprefix, Line, Irc

def parse_action(text):
    if text.startswith("\x01ACTION ") and text.endswith("\x01"):
        return True, text[len("\x01ACTION "):-1]
    else:
        return False, text

# the RDF vocabulary
rdf_type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

rdfs_label   = "http://www.w3.org/2000/01/rdf-schema#label"
rdfs_seeAlso = "http://www.w3.org/2000/01/rdf-schema#seeAlso"

owl_sameAs = "http://www.w3.org/2002/07/owl#sameAs"

dc_date           = "http://purl.org/dc/elements/1.1/date"
dcterms_created   = "http://purl.org/dc/terms/created"
xsd_dateTime      = "http://www.w3.org/2001/XMLSchema#dateTime"
sioc_container_of = "http://rdfs.org/sioc/ns#container_of"
sioc_has_creator  = "http://rdfs.org/sioc/ns#has_creator"
sioc_content      = "http://rdfs.org/sioc/ns#content"
sioc_Forum        = "http://rdfs.org/sioc/ns#Forum"
sioc_Post         = "http://rdfs.org/sioc/ns#Post"
sioc_User         = "http://rdfs.org/sioc/ns#User"
ds_item           = "http://fenfire.org/2007/03/discussion-summaries#item"
ds_occurrence     = "http://fenfire.org/2007/03/discussion-summaries#occurrence"

namespaces = [("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
              ("owl", "http://www.w3.org/2002/07/owl#"),
              ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
              ("dc", "http://purl.org/dc/elements/1.1/"),
              ("dcterms", "http://purl.org/dc/terms/"),
              ("xsd", "http://www.w3.org/2001/XMLSchema#"),
              ("sioc", "http://rdfs.org/sioc/ns#"),
              ("ds", "http://fenfire.org/2007/03/discussion-summaries#"),
              ]

class IrcFilter(Irc):
    def __init__(self, sink):
        self.sink = sink

    def close(self):
        if self.sink:
            self.sink.close()

class IrcSink(IrcFilter):
    def __init__(self):
        IrcFilter.__init__(self, None)

class ChannelFilter(IrcFilter):
    """A filter that only passes on lines related to a given channel"""
    def __init__(self, channel, sink):
        IrcFilter.__init__(self, sink)
        self.registered = False
        self.nick = None # nick
        self.user = None # user@host
        self.serverprefix = None # irc.jyu.fi
        self.clientprefix = None # nick!user@host
        self.channels = []
        self.away = False
        self.awaymsg = None

        self.namreply = {}

        self.interestingchannel = channel
        self.sink = sink
        self.nick2channels = {}
        self.channel2nicks = {}


    def isme(self, prefix):
        return parseprefix(prefix)[0] == self.nick

    def handleReceived(self, line):
        if line.prefix:
            nick,_ = parseprefix(line.prefix)
        else:
            nick = None
        relatedbefore = self.nick2channels.get(nick, [])
        Irc.handleReceived(self, line)
# FIXME: Many commands missing here!
        if line.cmd in ('NICK', 'QUIT'):
            if self.interestingchannel in relatedbefore:
                self.sink.handleReceived(line)
        elif line.cmd in ('JOIN','PART','KICK','PRIVMSG','NOTICE'):
            if line.args[0].lower() == self.interestingchannel:
                self.sink.handleReceived(line)
        elif line.cmd in ('366','332','333','329'):
            if line.args[1].lower() == self.interestingchannel:
                self.sink.handleReceived(line)
        elif line.cmd in ('353',):
            if line.args[2].lower() == self.interestingchannel:
                self.sink.handleReceived(line)
    handleReceivedFallback = lambda self,x:None

# state tracking:
    def irc_RPL_WELCOME(self, line):
        self.nick = line.args[0]

    def irc_NICK(self, line):
        # we get messages about other clients as well
        if self.isme(line.prefix):
            self.nick = line.args[0]
            self.clientprefix = self.nick + '!' + self.user
        oldnick,_ = parseprefix(line.prefix)
        newnick = line.args[0]
        self.nick2channels[newnick] = self.nick2channels[oldnick]
        del self.nick2channels[oldnick]
        for c in self.nick2channels[newnick]:
            i = self.channel2nicks[c].index(oldnick)
            self.channel2nicks[c][i] = newnick
            
    def irc_JOIN(self, line):
        channel = line.args[0].lower()
        if self.isme(line.prefix):
            self.channels.append(channel)
            self.channel2nicks[channel] = [] 
        nick,_ = parseprefix(line.prefix)
        if not nick in self.nick2channels:
            self.nick2channels[nick] = []
        self.nick2channels[nick].append(channel)
        self.channel2nicks[channel].append(nick)
    def irc_PART(self, line):
        channel = line.args[0].lower()
        if self.isme(line.prefix):
            self.channels.remove(channel)
            del self.channel2nicks[channel]
        else:
            nick,_ = parseprefix(line.prefix)
            self.nick2channels[nick].remove(channel)
            self.channel2nicks[channel].remove(nick)

    def irc_KICK(self, line):
        channel = line.args[0].lower()
        if line.args[1] == self.nick:
            self.channels.remove(channel)
            del self.channel2nicks[channel]
        else:
            nickword = line.args[1].lower()
            for n in self.nick2channels.keys():
                if n.lower() == nickword:
                    nick = n
            self.nick2channels[nick].remove(channel)
            self.channel2nicks[channel].remove(nick)

    def irc_QUIT(self, line):
        nick,_ = parseprefix(line.prefix)
        for c in self.nick2channels[nick]:
            self.channel2nicks[c].remove(nick)
        del self.nick2channels[nick]

#2008-09-25T18:32:40+03:00 :irc.jyu.fi 353 tuukkah_ = #footest :tuukkah_ @tuukkah
#2008-09-25T18:32:40+03:00 :irc.jyu.fi 366 tuukkah_ #footest :End of NAMES list.
    def irc_RPL_NAMREPLY(self, line):
        channel = line.args[2].lower()
        if not channel in self.namreply:
            self.namreply[channel] = []
        self.namreply[channel] += line.args[3].split(" ")

    def irc_RPL_ENDOFNAMES(self, line):
        channel = line.args[1].lower()
        newnicks = self.namreply.pop(channel)
        oldnicks = self.channel2nicks[channel]
        for n in oldnicks:
            self.nick2channels[n].remove(channel)
        self.channel2nicks[channel] = []
        for n in newnicks:
            if not n:
                continue
            nick = n.lstrip("@").lstrip("+")
            self.channel2nicks[channel].append(nick)
            if not nick in self.nick2channels:
                self.nick2channels[nick] = []
            self.nick2channels[nick].append(channel)

    def irc_RPL_UNAWAY(self, _):
        self.away = False
    def irc_RPL_NOWAWAY(self, _):
        self.away = True

class TimeFilter(IrcFilter):
    """A filter that only passes on lines whose time matches a given prefix"""
    def __init__(self, timeprefix, sink):
        IrcFilter.__init__(self, sink)
        self.timeprefix = timeprefix
        self.sink = sink
    def handleReceivedFallback(self, line):
        if line.time.startswith(self.timeprefix):
            self.sink.handleReceived(line)

class OffFilter(IrcFilter):
    """A filter that removes lines marked as off-the-record"""
    def irc_PRIVMSG(self, line):
        content = line.args[1]

        # XXX need to remove leading + or - from content?
        if content.startswith("[off]") or content.startswith("\1ACTION [off]"):
            return # hide off-record statements

        self.sink.handleReceived(line)

class HtmlSink(IrcSink):
    """A sink that renders the lines it receives as a HTML table"""
    def __init__(self, title, selfuri):
        IrcSink.__init__(self)
        print """<html>
<head>
<title>%s</title>
<link rel="meta" href="http://triplr.org/rdf/%s" type="application/rdf+xml" title="SIOC"/>
<style type="text/css"><!--
td {
    vertical-align: top;
}

td > a:target {
    background-color: lightblue;
}
--></style>
</head>
<body>
<h1>Experimental IRC log %s</h1>
<div style="color: 9999CC; background: #CCCCFF; border: 3px dashed; padding: 1em; margin: 1em;">
<p style="color: black; margin: 0">
These logs are provided as an experiment in indexing discussions using 
SIOC. 
</p>
</div>
<table>""" % (title, selfuri, title)

    def irc_PRIVMSG(self, line):
        id = line.time.split("T")[1] # FIXME not unique
        time = line.time.split("T")[1]
        nick,_acct = parseprefix(line.prefix)
        content = line.args[1]
        action, content = parse_action(content)
        if action:
            print """<tr>
<td><a name="%s" href="#%s">%s</a></td>
<td> * </td>
<td>%s %s</td>
</tr>""" % (id, id, time, self.escape_html(nick), self.escape_html(content))
        else:
            print """<tr>
<td><a name="%s" href="#%s">%s</a></td>
<td>&lt;%s&gt;</td>
<td>%s</td>
</tr>""" % (id, id, time, self.escape_html(nick), self.escape_html(content))

    handleReceivedFallback = lambda self,x:None

    def escape_html(self, s):
        # & needs to be escaped first, before more are introduced:
        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('"', '&quot;')
        return s

    def close(self):
        print """</table>
<p>Back to channel and daily index: <a href="/index">content-negotiated</a> <a href="/index.html">html</a> <a href="/index.turtle">turtle</a></p>

<p>Rendered by <a href="http://github.com/tuukka/sioclog/blob/master/sioclogwww.py">sioclogwww.py</a>.</p>
</body>
</html>"""

class TurtleSink(IrcSink):
    """A sink that renders the lines it receives as a Turtle RDF document"""
    def __init__(self, root, channel):
        IrcSink.__init__(self)
        self.root = root
        self.channel = channel
        self.channelID = self.channel.strip("#").lower()
        self.channelURI = self.root + self.channelID

        self.triples = []

        self.base = self.root

        for ns, uri in namespaces:
            print "@prefix %s: <%s> ." % (ns, self.turtle_escape(">", uri))
        print
        print "@base <%s> ." % (self.turtle_escape(">", self.base))
        print
        self.triples += [(self.channelURI, owl_sameAs, 
                          "irc://freenode/%23" + self.channelID),
                         (self.channelURI, rdf_type, sioc_Forum),
                         (self.channelURI, rdfs_label, 
                          PlainLiteral("#" + self.channel)),
                         ]

    def irc_PRIVMSG(self, line):
        self.triples += self.create_triples(line)
        
    def create_triples(self, line):
        id = line.time.split("T")[1] # FIXME not unique
        time = line.time # make sure this is in "Z"
        day = line.time.split("T")[0]
        second = line.time.split("T")[1]
        nick,_acct = parseprefix(line.prefix)
        rawcontent = line.args[1]

        file = self.channelID + "/" + day

        # XXX need to remove leading + or - from rawcontent?

        action, content = parse_action(rawcontent)

        if content.startswith("[off]"):
            return [] # hide off-record statements

        if action:
            label = " * " + nick + " " + content
        else:
            label = "<" + nick + "> " + content

        event = self.root + file + "#" + second # XXX + offset to make this unique
        timestamp = TypedLiteral(time, xsd_dateTime)

        creator = "irc://freenode/"+nick+",isuser"
        return [None, # adds a blank line for clarity
                (self.channelURI, sioc_container_of, event),
                (event, dcterms_created, timestamp),
                (event, sioc_has_creator, creator),
                (event, sioc_content, PlainLiteral(rawcontent)),
                (event, rdfs_label, PlainLiteral(label)),
                (event, rdf_type, sioc_Post),
                (creator, rdfs_label, PlainLiteral(nick)),
                (creator, rdf_type, sioc_User)]
    
    def close(self):
        for t in self.triples:
            if not t:
                print
            else:
                s,p,o = t
                print "%s %s %s ." % (self.show(s), self.show(p), self.show(o))

    def show(self, node):
        # FIXME escaping
        if isinstance(node, basestring): # URI
            if node.startswith(self.base):
                rest = node[len(self.base):]
                if self.base.endswith("/") and not rest.startswith("/"):
                    return "<" + self.turtle_escape(">", rest) + ">"
                # XXX detect more cases where we can use a relative URI...
            for ns, uri in namespaces:
                if node.startswith(uri): # XXX and the rest is an allowed name
                    return ns + ":" + node[len(uri):]
            return "<" + self.turtle_escape(">", node) + ">"
        elif isinstance(node, PlainLiteral):
            return '"' + self.turtle_escape('"', node.text) + '"'
        elif isinstance(node, TypedLiteral):
            return '"' + self.turtle_escape('"', node.text) + '"' + "^^" + self.show(node.literaltype)

    def turtle_escape(self, endchar, text):
        replacements = ([('\\', '\\\\'),
                         (endchar, '\\'+endchar),
                         ('\n', '\\n'),
                         ('\r', '\\r'),
                         ('\t', '\\t')] +
                        [(chr(c), '\\u%04x' % c) for c in range(0x20)+[0x7f]]
                        )
        for char, escape in replacements:
            text = text.replace(char, escape)
        return text

class PlainLiteral:
    """RDF plain literal"""
    def __init__(self, text):
        self.text = str(text)

class TypedLiteral:
    """RDF typed literal"""
    def __init__(self, text, literaltype):
        self.text = str(text)
        self.literaltype = literaltype

class RawSink(IrcSink):
    """A sink that prints the lines it receives raw but timestamped"""

    def handleReceivedFallback(self, line):
        print "%s %s" % (line.time,line)

class ChannelsAndDaysSink(IrcSink):
    """A sink that collects the channels and days of activity that it sees"""
    def __init__(self):
        IrcSink.__init__(self)

        self.channels = {}
        self.days = {}
        self.day2channels = {}

    def irc_PRIVMSG(self, line):
        id = line.time.split("T")[1] # FIXME not unique
        time = line.time # make sure this is in "Z"
        day = line.time.split("T")[0]

        target = line.args[0]
        if not target.startswith('#'):
            return
        channelName = target.strip("#").lower()
        
        self.days[day] = True
        self.channels[channelName] = True
        self.day2channels.setdefault(day, {})[channelName] = True

    handleReceivedFallback = lambda self,x:None

def run(inputstream, pipeline):
    """Processes each line from the input in the pipeline and closes it"""
    for l in inputstream:
        #print l
        time, linestr = l[:-1].split(" ",1)
        try:
            linestr = linestr.rstrip('\r') # according to RFC, there is \r
            pipeline.handleReceived(Line(linestr=linestr, time=time))
        except:
            print_exc()

    pipeline.close()

if __name__ == '__main__':
    # test main
    import sys
    root = sys.argv[1]
    channel = sys.argv[2]
    timeprefix = sys.argv[3]

    title = "%s-%s" % (channel, timeprefix)
    selfuri = "" # FIXME

    pipeline = OffFilter(ChannelFilter(channel, 
                                       TimeFilter(timeprefix, 
                                                  RawSink()
#                                                  HtmlSink(title, selfuri)
#                                                  TurtleSink(root, channel)
                                                  )))
    
    run(sys.stdin, pipeline)
