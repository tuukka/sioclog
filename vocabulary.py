#!/usr/bin/env python

"""vocabulary.py - a module for the RDF vocabularies used

Example usage:
from vocabulary import namespaces, RDF, RDFS, OWL, DC, DCTERMS, XSD, SIOC, DS
print RDF.type
"""

# the RDF vocabulary
class RDF(object):
    type = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

class RDFS(object):
    label   = "http://www.w3.org/2000/01/rdf-schema#label"
    seeAlso = "http://www.w3.org/2000/01/rdf-schema#seeAlso"

class OWL(object):
    sameAs = "http://www.w3.org/2002/07/owl#sameAs"

class DC(object):
    date           = "http://purl.org/dc/elements/1.1/date"

class DCTERMS(object):
    created   = "http://purl.org/dc/terms/created"

class XSD(object):
    dateTime      = "http://www.w3.org/2001/XMLSchema#dateTime"

class FOAF(object):
    primaryTopic = "http://xmlns.com/foaf/0.1/primaryTopic"
    topic = "http://xmlns.com/foaf/0.1/topic"
    holdsAccount = "http://xmlns.com/foaf/0.1/holdsAccount"
    homepage = "http://xmlns.com/foaf/0.1/homepage"
    weblog = "http://xmlns.com/foaf/0.1/weblog"
    nick = "http://xmlns.com/foaf/0.1/nick"
    name = "http://xmlns.com/foaf/0.1/name"
    firstName = "http://xmlns.com/foaf/0.1/firstName"
    img = "http://xmlns.com/foaf/0.1/img"
    depiction = "http://xmlns.com/foaf/0.1/depiction"
    knows = "http://xmlns.com/foaf/0.1/knows"

class SIOC(object):
    container_of = "http://rdfs.org/sioc/ns#container_of"
    has_creator  = "http://rdfs.org/sioc/ns#has_creator"
    content      = "http://rdfs.org/sioc/ns#content"
    Forum        = "http://rdfs.org/sioc/ns#Forum"
    Post         = "http://rdfs.org/sioc/ns#Post"
    User         = "http://rdfs.org/sioc/ns#User"
    space_of     = "http://rdfs.org/sioc/ns#space_of"
    links_to     = "http://rdfs.org/sioc/ns#links_to"
    has_subscriber = "http://rdfs.org/sioc/ns#has_subscriber"

class SIOCT(object):
    ChatChannel = "http://rdfs.org/sioc/types#ChatChannel"

class DS(object):
    item           = "http://fenfire.org/2007/03/discussion-summaries#item"
    occurrence     = "http://fenfire.org/2007/03/discussion-summaries#occurrence"

namespaces = [("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
              ("owl", "http://www.w3.org/2002/07/owl#"),
              ("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
              ("dc", "http://purl.org/dc/elements/1.1/"),
              ("dcterms", "http://purl.org/dc/terms/"),
              ("xsd", "http://www.w3.org/2001/XMLSchema#"),
              ("foaf", "http://xmlns.com/foaf/0.1/"),
              ("sioc", "http://rdfs.org/sioc/ns#"),
              ("sioct", "http://rdfs.org/sioc/types#"),
              ("ds", "http://fenfire.org/2007/03/discussion-summaries#"),
              ]
