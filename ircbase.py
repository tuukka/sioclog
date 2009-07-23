#!/usr/bin/env python

"""ircbase.py - a module for dealing with IRC connections and data

Example usage: 
import ircbase
ircbase.dbg = True
from ircbase import parseprefix, Line, Irc
class IrcFilter(Irc):
    ...
"""

from traceback import print_exc

from twisted.protocols import basic
from twisted.words.protocols import irc

def info(msg):
    print msg
err = info
dbg = False

### copy from irchub.py starts...

def parseprefix(prefix):
    """Splits a prefix in the IRC protocol into a nick and a login."""
    try:
        nick,acct = prefix.split('!')
    except ValueError: # server prefix has no nick
        nick,acct = None, prefix

    return nick,acct

class Line:
    """One (immutable) line of the IRC protocol.
    Constructed either from a command, arguments and source prefix, or
    from a string. Can also contain a reference to the sending client."""
    def __init__(self, cmd=None, args=None, prefix=None,
                 source=None, time=None, linestr=None):
        self.source = source
        self.time = time
        if linestr != None: self.init_linestr(linestr)
        else: self.init_words(cmd, args, prefix)
    def init_linestr(self, linestr):
        self.linestr = linestr
        # parse the line into a normalized form
        self.prefix, self.cmd, self.args = irc.parsemsg(linestr)
        if self.prefix == '': self.prefix = None
        self.cmd = self.cmd.upper()
    def init_words(self, cmd, args, prefix):
        if args == None: args = []
        cmd = cmd.upper()
        self.prefix, self.cmd, self.args = prefix, cmd, list(args)
        # create the string presentation from arguments
        if prefix == None: prefix = []
        else: prefix = [':' + prefix]
        if len(args) > 0 and ' ' in args[-1]: args[-1] = ':'+args[-1]
        self.linestr = ' '.join(prefix+[cmd]+args)

    def __str__(self):
        """Returns the protocol line as a string, based on the
        construction-time information."""
        return self.linestr

    __repr__ = __str__ # for nicer debug outputs

class Irc(basic.LineReceiver):
    delimiter = '\n' # LineReceiver splits by this, everybody doesn't send \r
    factory = None # set in instances by the factory
    """A connection using the IRC protocol."""
    def lineReceived(self, linestr):
        """Callback for messages received from client."""
        try:
            linestr = linestr.rstrip('\r') # according to RFC, there is \r
            if dbg: info("%s: %s" % (self.__class__.__name__, linestr))
            self.handleReceived(Line(linestr=linestr, source=self))
        except:
            print_exc()

    def handleReceived(self, line):
        """Handles received lines.
        Calls method irc_CMD, where CMD is the name of the command or
        reply in the line. If there is no such method, or if the method
        doesn't return True, handleReceivedFallback is called."""
        name = irc.numeric_to_symbolic.get(line.cmd, line.cmd)
        method = getattr(self, "irc_%s" % name, None)
        if method == None or not method(line):
            self.handleReceivedFallback(line) # if not handled otherwise

    def noHandler(self, line):
        if dbg: info("Line wasn't handled: %s" % line)
    handleReceivedFallback = noHandler

    def sendLine(self, line):
        """Sends a message to this connection."""
        self.transport.write(str(line)+'\r\n')

    def loseConnection(self):
        self.transport.loseConnection()

### ... copy from irchub.py ends
