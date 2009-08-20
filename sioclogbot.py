#!/usr/bin/env python

"""sioclogbot.py - an IRC bot that logs what it sees into a log file

Requires Twisted Python

Usage: 
sioclogbot.py server serverport nick user name channels logfile
For example:
sioclogbot.py irc.freenode.net 6667 sioc sioc "SIOC bot" "#sioc" sioc.log
"""

# ChangeLog:
# 2008-09-17: Reliable connecting and reconnecting

# TODO:
# * log splitting/rotating?
# * log enrichments?
# * www server?
# * unit tests

from __future__ import with_statement

from traceback import print_exc

from twisted.internet import protocol, reactor # you'll need python-twisted
from twisted.protocols import basic
from twisted.words.protocols import irc
from twisted.python.rebuild import rebuild

import ircbase
ircbase.dbg = True
from ircbase import parseprefix, Line, Irc, w3c_timestamp

import sioclogbot # XXX import myself for rebuild

def info(msg):
    print msg
err = info
dbg = True


class IrcServer(Irc):
    """Connection to the server."""
    def __init__(self):
        self.registered = False # whether the server has welcomed us
        self.nick = None # nick
        self.user = None # user@host
        self.serverprefix = None # irc.jyu.fi
        self.clientprefix = None # nick!user@host
        self.channels = [] # the channels we are currently on
        self.away = False # whether we are currently marked as being away
        self.awaymsg = None # the away message we have last requested

        self.timeoutCall = None # processed if server doesn't reply to PING

        # these are used to filter expected replies from the logs:
        self.whoreq = {} # pending WHO requests, channel -> client list
        self.whorep = {} # ongoing WHO responses, channel -> client list
        self.pingreq = {} # pending PING requests, token -> anything
        self.topicreq = {} # pending TOPIC requests, channel -> client list
        self.modereq = {} # pending MODE requests, channel -> client list
        self.namesreq = {} # pending NAMES requests, channel -> client list
        self.namesrep = {} # ongoing NAMES responses, channel -> client list

    def isme(self, prefix):
        return parseprefix(prefix)[0] == self.nick

    # basic IRC client functionality:
    def connectionMade(self):
        info("Server connected!")
        self.factory.instance = self
        self.sendLine(Line("NICK",[self.factory.nick]))
        self.sendLine(Line("USER",[self.factory.user, "*", "*",
                                   self.factory.name]))
        self.timeoutCall = reactor.callLater(2*60, self.pingTimeout) # XXX

    def connectionLost(self, reason):
        err("Disconnected from server: %s" % reason.value)
        # FIXME Don't log if already logged as a QUIT
        self.logLine(Line('ERROR', ['Closing Link: %s[%s] (%s)'
                                    % (self.nick,
                                       self.user, reason.value)]))
        # XXX what else? inform clients?
        self.factory.instance = None

    def logLine(self, line):
        self.factory.logLine(line)
    handleReceivedFallback = logLine


    def irc_ERR_NICKNAMEINUSE(self, line):
        self.sendLine(Line("NICK", [line.args[1]+'_']))

    def irc_ERR_UNAVAILRESOURCE(self, line):
        if line.args[1][0] is not '#':
            self.irc_ERR_NICKNAMEINUSE(line)

    def irc_RPL_WELCOME(self, line):
        self.registered = True
        self.serverprefix = line.prefix
        self.nick = line.args[0]
        _, self.user = parseprefix(line.args[-1].split(' ')[-1])
        self.clientprefix = "%s!%s" % (self.nick, self.user)

        if self.timeoutCall:
            self.timeoutCall.cancel()
            self.timeoutCall = None

        self.ping()

        # enable + or - prefix on each msg indicating 
        self.sendLine(Line("CAPAB", ["IDENTIFY-MSG"]))

        for c in self.factory.channels:
            self.sendLine(Line("JOIN", [c]))
            
        if dbg: info("store: %s" % self.factory.store)
        for line in self.factory.store:
            self.sendLine(line)
        self.factory.store = []

        return False

    def irc_PING(self, line):
        self.sendLine(Line("PONG",[line.args[0]]))
        return True # don't log

    def irc_PONG(self, line):
        if line.args[1] in self.pingreq:
            del self.pingreq[line.args[1]]

            if line.args[1] == 'KEEPALIVE' and self.timeoutCall:
                self.timeoutCall.cancel()
                self.timeoutCall = None
                reactor.callLater(5*60, self.ping)

            return True # don't log
        else: return False

    def irc_PRIVMSG(self, line):
        msg = line.args[1]

        if line.args[0].startswith("#"):
            if msg[1:].startswith(self.nick):
                if msg[1+len(self.nick)+1:].strip() == "pointer":
                    answerURI = self.factory.rootURI + line.args[0][1:].lower() + '/' + line.ztime.rstrip("Z").replace("T", "#")
                    answer = "That line is " + answerURI
                    self.sendLine(Line("NOTICE", [line.args[0], answer]))

        if line.args[0] != self.nick:
            return False # not to us
        if parseprefix(line.prefix)[0] != self.factory.admin:
            return False # not from admin

        if msg == "+rebuild":
            try:
                rebuild(sioclogbot)
                info("rebuilt")
            except:
                print_exc()
        elif msg.startswith("+do "):
            try:
                self.sendLine(Line(linestr=msg[len("+do "):]))
            except:
                print_exc()

        return False # log

    # response filtering:
    def filter_oneline(self, reqlist, line, argindex = 1):
        obj = line.args[argindex]
        reps = reqlist.pop(obj, 'all')
        if reps != 'all':
            for rep in reps:
                rep.sendLine(line)
            return True # filter from others
        else: return False
    def filter_dataline(self, reqlist, replist, line, argindex = 1):
        """Filters data lines of data-end-replies from those who didn't
        request them. After the request is sent, this may be called several
        times."""
        obj = line.args[argindex]
        reps = replist.get(obj, None) # who the reply is going to
        if reps == None: # if new reply:
            # turn requestors into recipients, or 'all' if nobody specifically
            reps = replist[obj] = reqlist.pop(obj, 'all')
        if reps != 'all':
            for rep in reps:
                rep.sendLine(line)
            return True # filter from others
        else: return False
    def filter_endline(self, reqlist, replist, line):
        """Filters end lines from data-end-replies from those who didn't
        request them. There might have been data lines before this, or not."""
        obj = line.args[1]
        reps = replist.pop(obj, None) # who the replies were to
        if reps == None: # if there were no data lines:
            reps = reqlist.pop(obj, 'all') # take requestors
        if reps != 'all':
            for rep in reps:
                rep.sendLine(line)
            return True # filter from others
        else: return False
    def irc_RPL_WHOREPLY(self, line):
        return self.filter_dataline(self.whoreq, self.whorep, line)
    def irc_RPL_ENDOFWHO(self, line):
        return self.filter_endline(self.whoreq, self.whorep, line)
    def irc_RPL_TOPIC(self, line):
        return self.filter_oneline(self.topicreq, line)
    irc_RPL_NOTOPIC = irc_RPL_TOPIC
    def irc_RPL_CHANNELMODEIS(self, line):
        return self.filter_oneline(self.modereq, line)
    def irc_RPL_UMODEIS(self, line):
        return self.filter_oneline(self.modereq, line, argindex=0)
    def irc_RPL_NAMREPLY(self, line):
        return self.filter_dataline(self.namesreq, self.namesrep, line,
                                    argindex=2)
    def irc_RPL_ENDOFNAMES(self, line):
        return self.filter_endline(self.namesreq, self.namesrep, line)

    # state tracking:
    def irc_NICK(self, line):
        # we get messages about other clients as well
        if self.isme(line.prefix):
            self.nick = line.args[0]
            self.clientprefix = self.nick + '!' + self.user
    def irc_JOIN(self, line):
        if self.isme(line.prefix):
            # we first get the real self.user from server here
            _, self.user = parseprefix(line.prefix)
            self.clientprefix = self.nick + '!' + self.user
            self.channels.append(line.args[0])
    def irc_PART(self, line):
        if self.isme(line.prefix):
            self.channels.remove(line.args[0])
    def irc_KICK(self, line):
        if line.args[1] == self.nick:
            self.channels.remove(line.args[0])
    def irc_RPL_UNAWAY(self, _):
        self.away = False
    def irc_RPL_NOWAWAY(self, _):
        self.away = True

    def addRequest(self, list, line):
        """Add the request in the line to the list."""
        obj = line.args[0]
        list[obj]=list.get(obj, []) + [line.source]
        # if request pending, don't send another: XXX timeout?
        if len(list[obj]) > 1: return True
        else: return False

    # actions:
    def sendLine(self, line):
        """send line to server, and add outbound requests to lists."""
        if line.cmd == 'PING':
            self.pingreq[line.args[0]] = True
        if line.cmd == 'WHO':
            self.addRequest(self.whoreq, line)
        if line.cmd == 'TOPIC' and len(line.args) == 1:
            self.addRequest(self.topicreq, line)
        if line.cmd == 'MODE' and len(line.args) == 1:
            self.addRequest(self.modereq, line)
        if line.cmd == 'NAMES':
            self.addRequest(self.namesreq, line)
        if line.cmd == 'AWAY':
            if len(line.args) > 0 and line.args[0] != '': # if setting away:
                self.awaymsg = line.args[0]
        if line.cmd in ["PRIVMSG", "NOTICE"]:
            # need to log self. simulate server info:
            fakeargs = line.args
            fakeargs[1] = "+" + fakeargs[1] # we are "identified"
            fakeline = Line(cmd=line.cmd, args=fakeargs,
                              prefix=self.clientprefix, time=w3c_timestamp())
            # log the line *after* the line currently being processed
            reactor.callLater(0, self.logLine, fakeline)
        if dbg: info("Sent to server: %s" % line)
        Irc.sendLine(self, line)

    def ping(self):
        self.sendLine(Line("PING", ["KEEPALIVE"]))
        self.timeoutCall = reactor.callLater(5*60, self.pingTimeout)

    def pingTimeout(self):
        self.timeoutCall = None
        self.loseConnection("Pong timeout")

    def loseConnection(self, reason="No reason"):
        self.sendLine(Line('QUIT', [reason]))
        self.logLine(Line('ERROR', ['Closing Link: %s[%s] (%s)'
                                    % (self.nick,
                                       self.user, reason)]))
        # XXX wait some time?
        Irc.loseConnection(self)
        

class IrcServerFactory(protocol.ClientFactory):
    """Factory that will create an IrcServer object per connection."""
    protocol = IrcServer

    def __init__(self, server, serverport, nick, user, name, channels, logname, admin, rootURI):
        self.server = server
        self.serverport = serverport
        self.nick = nick
        self.user = user
        self.name = name
        self.channels = channels
        self.logname = logname
        self.admin = admin
        self.rootURI = rootURI

        self.store = [] # lines sent before we had a connection to the server
        self.backoff = None # fail fast if we can't make the first connection
        self.instance = None # the IrcServer object for the current connection

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        err("Connection to server lost: %s" % reason.value)
        self.backoff = 5 # seconds. setting this starts retrying connects
        connector.connect()
        
    def clientConnectionFailed(self, connector, reason):
        """If connecting fails, schedule a retry."""
        err("Couldn't connect server: %s" % reason.value)
        if self.backoff != None:
            # XXX ReconnectingClientFactory implements jitter, we don't
            reactor.callLater(self.backoff, connector.connect)
            self.backoff = self.backoff * 2
        else:
            reactor.stop()

    def logLine(self, line):
        with file(self.logname, "ab") as logfile:
            logfile.write("%s %s\r\n" % (line.time, line))
            logfile.flush()

# first when started, initiate a connection to the server
if __name__ == "__main__":
    import sys
    try:
        server = sys.argv[1]
        serverport = int(sys.argv[2])
        nick = sys.argv[3]
        user = sys.argv[4]
        name = sys.argv[5]
        channels = sys.argv[6].split(",")
        logfile = sys.argv[7]
        admin = sys.argv[8]
        rootURI = sys.argv[9]
    except Exception, e:
        err(str(e))
        err("Usage: %s server serverport nick user name channels logfile admin"
            % sys.argv[0])
        sys.exit(5)
    info("i am %s!%s :%s" % (nick, user, name))
    info("planning to join the channels %s" % repr(channels))
    info("connecting to %s on port %d..." % (server, serverport))
    reactor.connectTCP(server, serverport,
                       sioclogbot.IrcServerFactory(server, serverport,
                                                   nick, user, name,
                                                   channels, logfile, 
                                                   admin, rootURI))
    info("entering main loop...")
    reactor.run()
    info("main loop done")
