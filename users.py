#!/usr/bin/env python

"""users.py - a module for dealing with users

Example usage: 
XXX
"""

import sys
from traceback import print_exc

from turtle import PlainLiteral, TypedLiteral, TurtleWriter
from vocabulary import namespaces, RDF, RDFS, OWL, FOAF, SIOC

from templating import new_context, get_template, expand_template
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
    try:
        global Red
        import RDF as Red
        m = Red.Model()
        # XXX name='guess' fails as twisted sends Content-type, not Content-Type
        m.load("http://localhost:3456/%s" % nick, name='turtle')
        for t in m.find_statements(Red.Statement(None, Red.Uri(FOAF.holdsAccount), Red.Uri("irc://freenode/%s,isnick" % nick))):
            return str(t.subject.uri)
    except:
        print_exc()
    else:
        print >>sys.stderr, "No webid for %s from taxonomybot" % nick

    print >>sys.stderr, "Falling back to get_nick2people()"

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
            yield html_escape(value.literal_value['string'])
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

def render_user_index(format, crumbs, datarooturi, datauri):
    freenodeURI = datarooturi + "#freenode"
    nicks = get_nicks()
    if format == "html":
        context = new_context()
        context.addGlobal('crumbs', crumbs)
        context.addGlobal('datarooturi', datarooturi)
        context.addGlobal('datauri', datauri)

        users = []
        for nick in nicks:
            user = "http://irc.sioc-project.org/users/%s#user" % nick
            users.append({'uri': user, 'nick': nick})

        context.addGlobal('users', users)

        template = get_template('users')
        expand_template(template, context)

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

def render_user(format, crumbs, datarooturi, nick, datauri):
    global Red
    import RDF as Red

    person = find_person(nick)

    error = None

    model = Red.Model()
    # XXX work around a bug in Redland?
    if person:
        try:
            model.load(person.rsplit('#', 1)[0], name='guess')
        except:
            error = "Error loading the FOAF info: %s" % sys.exc_info()[1]
 
    if format == "html":
        context = new_context()
        context.addGlobal('crumbs', crumbs)
        context.addGlobal('datarooturi', datarooturi)
        context.addGlobal('datauri', datauri)
        context.addGlobal('error', error)

        info = []
        if person:
            for name in link_values(model, person, [FOAF.name, FOAF.firstName, FOAF.nick, RDFS.label]):
                info.append({'key': 'Name', 'value': "%s" % name})
            for website in link_values(model, person, [FOAF.homepage]):
                info.append({'key': 'Website', 'value': "%s" % website})
            for weblog in link_values(model, person, [FOAF.weblog]):
                info.append({'key': 'Weblog', 'value': "%s" % weblog})
            for img in image_values(model, person, [FOAF.depiction, FOAF.img]):
                info.append({'key': 'Image', 'value': "%s" % img})
            for known in friend_values(model, person, [FOAF.knows]):
                info.append({'key': 'Knows', 'value': "%s" % known})

        context.addGlobal('here', {'nick': nick,
                                   'person': {'webid': person,
                                              'info': info}})

        template = get_template('user')
        expand_template(template, context)

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
