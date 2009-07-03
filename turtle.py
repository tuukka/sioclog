#!/usr/bin/env python

"""turtle.py - a module for RDF data in the Turtle syntax

Example usage:
from turtle import PlainLiteral, TypedLiteral, TurtleWriter
writer = TurtleWriter(self.base, namespaces)
writer.write([(creator, RDFS.label, PlainLiteral(nick))])
writer.close()
"""

class TurtleWriter(object):
    def __init__(self, base=None, namespaces=None):
        self.base = base
        if namespaces is not None:
            self.namespaces = namespaces
        else:
            self.namespaces = []

        print

        for ns, uri in self.namespaces:
            print "@prefix %s: <%s> ." % (ns, self.turtle_escape(">", uri))

        if self.base:
            print
            print "@base <%s> ." % (self.turtle_escape(">", self.base))

        print

    def write(self, triples):
        for t in triples:
            if not t:
                print
            else:
                s,p,o = t
                print "%s %s %s ." % (self.show(s), self.show(p), self.show(o))

    def close(self):
        pass

    def show(self, node):
        if isinstance(node, basestring): # URI
            if self.base and node.startswith(self.base):
                rest = node[len(self.base):]
                if self.base.endswith("/") and not rest.startswith("/"):
                    return "<" + self.turtle_escape(">", rest) + ">"
                # XXX detect more cases where we can use a relative URI...
            for ns, uri in self.namespaces:
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
