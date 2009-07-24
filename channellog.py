#!/usr/bin/env python

"""channellog.py - a module for filtering and rendering streams of IRC data

Example usage:
from channellog import OffFilter, ChannelFilter, TimeFilter, HtmlSink, TurtleSink, RawSink, ChannelsAndDaysSink, run
pipeline = ChannelFilter("#sioc", RawSink())
run(file("sioc.log"), pipeline)
"""

import sys, re, datetime

from traceback import print_exc

import ircbase
ircbase.dbg = False
from ircbase import parseprefix, Line, Irc

from templating import new_context, get_template, expand_template
from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, DC, DCTERMS, XSD, FOAF, SIOC, SIOCT, DS

datetimere = r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?"
timezonere = r"(Z|(\+|-)(\d{2}):(\d{2}))"
timere = re.compile(datetimere + timezonere)
def convert_timestamp_to_z(text):
    # 2009-07-04T15:14:21.231+03:00
    match = timere.match(text)
    if match and match.group(0) == text:
        if match.groups()[7] == "Z":
            return text
        else:
            localtime = datetime.datetime(*map(int, match.groups()[:6]))
            fraction = match.groups()[6] or ""
            tzsign, tzhours, tzminutes = match.groups()[8:]
            distance = datetime.timedelta(hours=int(tzhours), 
                                          minutes=int(tzminutes))
            if tzsign == "-":
                utctime = localtime + distance
            else:
                utctime = localtime - distance
            return utctime.isoformat() + fraction + "Z"
    return

def parse_action(text):
    if text.startswith("\x01ACTION ") and text.endswith("\x01"):
        return True, text[len("\x01ACTION "):-1]
    else:
        return False, text


class IrcFilter(Irc):
    def __init__(self, sink):
        self.sink = sink

    def close(self):
        if self.sink:
            self.sink.close()

class IrcSink(IrcFilter):
    def __init__(self):
        IrcFilter.__init__(self, None)

class AddZTimeFilter(IrcFilter):
    def handleReceivedFallback(self, line):
        line.ztime = convert_timestamp_to_z(line.time)
        self.sink.handleReceived(line)

class AddRegisteredFilter(IrcFilter):
    def irc_PRIVMSG(self, line):
        content = line.args[1]
        if content[0] in ["+", "-"]:
            line.registered = content[0]
            line.args[1] = content[1:]
        else:
            line.registered = None

    irc_NOTICE = irc_PRIVMSG

    def handleReceivedFallback(self, line):
        self.sink.handleReceived(line)


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

        # reset state from previous connects:

        self.channels = []
        self.away = False
        self.awaymsg = None

        self.namreply = {}

        self.nick2channels = {}
        self.channel2nicks = {}

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
        if line.ztime.startswith(self.timeprefix):
            self.sink.handleReceived(line)

class OffFilter(IrcFilter):
    """A filter that removes lines marked as off-the-record"""
    def irc_PRIVMSG(self, line):
        content = line.args[1]

        # XXX need to remove leading + or - from content?
        if content.startswith("[off]") or content.startswith("\1ACTION [off]"):
            return True # hide off-record statements

    def handleReceivedFallback(self, line):
        self.sink.handleReceived(line)

class HtmlSink(IrcSink):
    """A sink that renders the lines it receives as a HTML table"""
    def __init__(self, crumbs, root, channel, timeprefix, selfuri):
        IrcSink.__init__(self)

        self.crumbs = crumbs
        self.root = root
        self.channel = channel
        self.timeprefix = timeprefix
        self.datauri = selfuri

        self.title = "#%s on %s" % (channel, timeprefix)

        self.events = []

    def irc_PRIVMSG(self, line):
        id = line.ztime.split("T")[1][:-1] # FIXME not unique
        time = id.split(".")[0]
        nick,_acct = parseprefix(line.prefix)
        content = line.args[1]
        creator = self.root + "users/" + nick + "#user"
        action, content = parse_action(content)
        self.events.append({'id': id, 'time': time, 
                            'isAction': action,
                            'creator': creator, 'nick': nick, 
                            'content': content.decode("utf-8")})

    handleReceivedFallback = lambda self,x:None

    def close(self):
        context = new_context()
        context.addGlobal('crumbs', self.crumbs)
        context.addGlobal('datarooturi', self.root)
        context.addGlobal('datauri', self.datauri)

        channelID = self.channel.strip("#").lower()
        channelURI = self.root + channelID + "#channel"

        context.addGlobal('channel', {'name': channelID,
                                      'uri': channelURI})
        context.addGlobal('timeprefix', self.timeprefix)

        context.addGlobal('title', self.title)

        context.addGlobal('events', self.events)

        template = get_template('channellog')
        expand_template(template, context)


class TurtleSink(IrcSink):
    """A sink that renders the lines it receives as a Turtle RDF document"""
    def __init__(self, root, channel, timeprefix):
        IrcSink.__init__(self)
        self.root = root
        self.channel = channel
        self.timeprefix = timeprefix
        self.channelID = self.channel.strip("#").lower()
        self.channelURI = self.root + self.channelID + "#channel"

        oldChannelURI = "irc://freenode/%23" + self.channelID

        self.triples = []
        self.base = self.root
        self.seenNicks = {}

        self.triples += [(self.channelURI, OWL.sameAs, oldChannelURI),
                         (self.channelURI, RDF.type, SIOC.Forum),
                         (self.channelURI, RDF.type, SIOCT.ChatChannel),
                         (self.channelURI, RDFS.label, 
                          PlainLiteral("#" + self.channel)),
                         ]

    def irc_PRIVMSG(self, line):
        self.triples += self.create_triples(line)
        
    def create_triples(self, line):
        id = line.ztime.split("T")[1][:-1] # FIXME not unique
        time = line.ztime
        day = line.ztime.split("T")[0]
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

        event = self.root + file + "#" + id
        timestamp = TypedLiteral(time, XSD.dateTime)

        self.seenNicks[nick] = nick

        creator = self.root + "users/" + nick + "#user"

        return [None, # adds a blank line for clarity
                (self.channelURI, SIOC.container_of, event),
                (event, DCTERMS.created, timestamp),
                (event, SIOC.has_creator, creator),
                (event, SIOC.content, PlainLiteral(rawcontent)),
                (event, RDFS.label, PlainLiteral(label)),
                (event, RDF.type, SIOC.Post),
                ]

    def close(self):
        for nick in self.seenNicks:
            creator = self.root + "users/" + nick + "#user"
            oldCreator = "irc://freenode/" + nick + ",isuser"
                
            self.triples += [None,
                             (creator, OWL.sameAs, oldCreator),
                             (creator, RDFS.label, PlainLiteral(nick)),
                             (creator, RDF.type, SIOC.User),
                             ]

        writer = TurtleWriter(None, namespaces)
        title = "Log of #%s on %s" % (self.channel, self.timeprefix)
        writer.write([("", RDFS.label, PlainLiteral(title)),
                      ("", FOAF.primaryTopic, self.channelURI),
                      ])
        writer.setBase(self.base)
        writer.write(self.triples)
        writer.close()


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
        self.channel2days = {}

    def irc_PRIVMSG(self, line):
        time = line.ztime
        day = time.split("T")[0]

        target = line.args[0]
        if not target.startswith('#'):
            return
        channelName = target.strip("#").lower()
        
        self.days[day] = True
        self.channels[channelName] = True
        self.day2channels.setdefault(day, {})[channelName] = True
        self.channel2days.setdefault(channelName, {})[day] = True

    handleReceivedFallback = lambda self,x:None


class TaxonomySink(IrcSink):
    """A sink that collects the NickServ taxonomy information it sees"""
    def __init__(self):
        IrcSink.__init__(self)

        self.taxonomy_state = None
        self.taxonomy_response = None
        self.taxonomy = {}

    def irc_NOTICE(self, line):
        if line.args[0].startswith("#"):
            return False
        if not line.prefix or parseprefix(line.prefix)[0] != "NickServ":
            return False

        msg = line.args[1]
        if msg.startswith("Taxonomy for \2"):
            nick = msg[len("Taxonomy for \2"):-2]
            self.taxonomy_state = nick
            self.taxonomy_response = []
        elif (msg.startswith("End of \2") or 
              msg.endswith("\2 is not registered.")):
            self.taxonomy[self.taxonomy_state] = self.taxonomy_response
            self.taxonomy_state = self.taxonomy_response = None
        elif self.taxonomy_state:
            key, rest = msg.split(" ", 1)
            value = rest.split(":", 1)[1][1:]
            self.taxonomy_response.append((self.taxonomy_state, key, value))


def run(inputstream, pipeline):
    """Processes each line from the input in the pipeline and closes it"""
    pipeline = AddRegisteredFilter(AddZTimeFilter(pipeline))
    for i, l in enumerate(inputstream):
        #print l
        time, linestr = l[:-1].split(" ",1)
        try:
            linestr = linestr.rstrip('\r') # according to RFC, there is \r
            pipeline.handleReceived(Line(linestr=linestr, time=time))
        except:
            print_exc()
            print >>sys.stderr, "... on line %s: %s" % (i+1, l)

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
