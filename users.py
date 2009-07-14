#!/usr/bin/env python

"""users.py - a module for dealing with users

Example usage: 
XXX
"""

import sys

from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, FOAF, SIOC

from htmlutil import escape_html as html_escape, escape_htmls as html_escapes

mttlbot_knowledge = None

def get_mttlbot_knowledge():
    global mttlbot_knowledge
    if mttlbot_knowledge is not None:
        return mttlbot_knowledge
    global Red
    import RDF as Red
    m = mttlbot_knowledge = Red.Model()
    # XXX for some reason, need to hardcode the returned content-type
    m.load("http://buzzword.org.uk/2009/mttlbot/graphs/knowledge", 
           name='guess')
    return m

def get_nick2people():
    m = get_mttlbot_knowledge()
    nick2people = {}
    for t in m.find_statements(Red.Statement(None, Red.Uri(FOAF.holdsAccount), None)):
        nick = str(t.object.uri).rsplit(",", 1)[0][len("irc://192.168.100.27/"):]
        nick2people[nick] = str(t.subject.uri)
    return nick2people

def get_nicks():
    return sorted(get_nick2people())

def find_person(nick):
    nick2people = get_nick2people()
    return nick2people.get(nick, None)

def get_values(model, subject, properties):
    values = []
    for property in properties:
        values += model.get_targets(Red.Uri(subject), Red.Uri(property))
        if values: break
        
    if values:
        for value in values:
            if value.is_resource():
                yield value
            elif value.is_literal():
                yield value
    else:
        yield None

def link_values(model, subject, property):
    values = get_values(model, subject, property)
    
    for value in values:
        if value is None:
            yield None
        elif value.is_literal():
            yield html_escape(value.literal_value['string'].encode('utf-8'))
        elif value.is_resource():
            yield """<a href="%s">%s</a>""" % html_escapes(value.uri, value.uri)

def image_values(model, subject, property):
    values = get_values(model, subject, property)
    
    for value in values:
        if value is None:
            yield None
        elif value.is_literal():
            yield html_escape(value.literal_value['string'])
        elif value.is_resource():
            yield """<img src="%s" />""" % html_escapes(value.uri)

def friend_values(model, subject, property):
    values = get_values(model, subject, property)
    nick2people = get_nick2people()
    for value in values:
        if value is None:
            yield None
        elif value.is_literal():
            yield html_escape(value.literal_value['string'])
        elif value.is_resource():
            for nick,person in nick2people.items():
                if str(value.uri) == person:
                    user = "http://irc.sioc-project.org/users/%s#user" % nick
                    yield """<a href="%s">%s</a>""" % html_escapes(user, nick)

def get_triples(model, subject, properties):
    for property in properties:
        values = model.get_targets(Red.Uri(subject), Red.Uri(property))
        for value in values:
            if value.is_resource():
                yield (subject, property, value.uri)
            elif value.is_literal():
                yield (subject, property, PlainLiteral(value.literal_value['string']))

def render_user_index(format, datarooturi, datauri):
    freenodeURI = datarooturi + "#freenode"
    nicks = get_nicks()
    if format == "html":
        print """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html 
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>%s</title>
<link rel="meta" href="http://triplr.org/rdf/%s" type="application/rdf+xml" title="SIOC"/>
""" % html_escapes("User index", datauri)

        print """<h1>Some IRC users</h1>"""
        print """<p>Available formats: <a href="%s">content-negotiated</a> <a href="%s.html">html</a> <a href="%s.turtle">turtle</a> (see <a href="http://sioc-project.org">SIOC</a> for the vocabulary) </p>""" % html_escapes(datauri, datauri, datauri)
        print """
<p>This list contains those users of Freenode IRC whose Web ID is known. <em>If you'd like to 
participate, please join channel #swig or #mttlbot-testing, and tell 
<a href="http://buzzword.org.uk/2009/mttlbot/#bot">mttlbot</a> your Web ID.</em></p>
<ul>"""
        for nick in nicks:
            user = "http://irc.sioc-project.org/users/%s#user" % nick
            print """<li><a href="%s">%s</a></li>""" % html_escapes(user, nick)
    elif format == "turtle":
        triples = []
        for nick in nicks:
            user = "http://irc.sioc-project.org/users/%s#user" % nick
            triples += [(freenodeURI, SIOC.space_of, user),
                        (user, RDFS.label, PlainLiteral(nick)),
                        (user, RDF.type, SIOC.User)]

        writer = TurtleWriter(None, namespaces)
        title = "User index"
        writer.write([("", RDFS.label, PlainLiteral(title)),
                      ("", FOAF.primaryTopic, freenodeURI)])
        writer.write(triples)
        writer.close()

def render_user(format, datarooturi, nick, datauri):
    global Red
    import RDF as Red

    person = find_person(nick)

    model = Red.Model()
    # XXX work around a bug in Redland?
    if person:
        try:
            model.load(person.rsplit('#', 1)[0], name='guess')
        except:
            if format == "html":
                print """Error loading the FOAF info: %s""" % html_escape(sys.exc_info()[1])
 
    if format == "html":
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
th {
    text-align: left;
}
th, td { 
    vertical-align: top;
}
img {
    border: none;
    margin: 1em;
}
--></style>
</head>
<body>""" % html_escapes("User %s" % nick, datauri)

        print """<h1>User %s</h1>""" % html_escape(nick)
        print """<p>Available formats: <a href="%s">content-negotiated</a> <a href="%s.html">html</a> <a href="%s.turtle">turtle</a> (see <a href="http://sioc-project.org">SIOC</a> for the vocabulary) </p>""" % html_escapes(datauri, datauri, datauri)
        print """
<table><tr><td>
<img src="http://irc.sioc-project.org/images/foaf.png" align="left" />
</td><td>"""
        if person:
            print """
<p>The person holding this user account has the Web ID (FOAF) of <br />
<tt><a href="%s">%s</a></tt>.
</p>
</td></tr></table>
""" % html_escapes(person, person)
            print "<table>"
            for name in link_values(model, person, [FOAF.name, FOAF.firstName, FOAF.nick, RDFS.label]):
                print "<tr><th>Name</th><td>%s</td></tr>" % name
            for website in link_values(model, person, [FOAF.homepage]):
                print "<tr><th>Website</th><td>%s</td></tr>" % website
            for weblog in link_values(model, person, [FOAF.weblog]):
                print "<tr><th>Weblog</th><td>%s</td></tr>" % weblog
            for img in image_values(model, person, [FOAF.depiction, FOAF.img]):
                print "<tr><th>Image</th><td>%s</td></tr>" % img
            for known in friend_values(model, person, [FOAF.knows]):
                print "<tr><th>Knows</th><td>%s</td></tr>" % known
            print "</table>"
        else:
            print """
<p>Nothing known about this person, because no Web ID (FOAF) known for this 
user. <em>If you are this person, please join channel #swig or #mttlbot-testing, and tell 
<a href="http://buzzword.org.uk/2009/mttlbot/#bot">mttlbot</a> your Web ID.</em></p>
</td></tr></table>"""
        print """
<p>Back to user index: <a href="/users">content-negotiated</a> <a href="/users.html">html</a> <a href="/users.turtle">turtle</a></p>

<p>Rendered by <a href="http://github.com/tuukka/sioclog">sioclog</a>.</p>
</body>
</html>"""
    elif format == "turtle":
        userURI = "http://irc.sioc-project.org/users/%s#user" % nick
        oldUserURI = "irc://freenode/%s,isuser" % nick
        triples = [None,
                   (datarooturi + "#freenode", SIOC.space_of, userURI),
                   (userURI, OWL.sameAs, oldUserURI),
                   (userURI, RDFS.label, PlainLiteral(nick)),
                   (userURI, RDF.type, SIOC.User),
                   ]
        if person:
            triples += [None, (person, FOAF.holdsAccount, userURI)]
            triples += get_triples(model, person, [FOAF.name, FOAF.firstName, FOAF.nick, RDFS.label])
        writer = TurtleWriter(None, namespaces)
        title = "About user %s" % nick
        writer.write([("", RDFS.label, PlainLiteral(title)),
                      ("", FOAF.primaryTopic, userURI),
                      ])
        writer.write(triples)
        writer.close()

if __name__ == '__main__':
    import sys
    nick = sys.argv[1]
    print "Looking up nick %s..." % nick
    person = find_person(nick)
    print "Person: %s" % person
    
    import RDF as Red
    
    model = Red.Model()
    # XXX work around a bug in RDF?
    model.load(person.rsplit('#', 1)[0], name='guess')
#    print model
#    for t in model.find_statements(RDF.Statement(RDF.Uri(person), None, None)):
#        print t.predicate, t.object

    for name in link_values(person, [FOAF.name]):
        print "Name: %s" % name
    for website in link_values(person, [FOAF.homepage]):
        print "Website: %s" % website
    for weblog in link_values(person, [FOAF.weblog]):
        print "Weblog: %s" % weblog
    for img in image_values(person, [FOAF.img]):
        print "Image: %s" % img
