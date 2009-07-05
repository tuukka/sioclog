#!/usr/bin/env python

"""users.py - a module for dealing with users

Example usage: 
XXX
"""

from vocabulary import FOAF

mttlbot_knowledge_nt = """
<http://www.kjetil.kjernsmo.net/foaf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kjetilkWork,isnick> .
<http://www.kjetil.kjernsmo.net/foaf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/KjetilK,isnick> .
<http://www.dajobe.org/foaf.rdf#i> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/dajobe,isnick> .
<http://kidehen.idehen.net/dataspace/person/kidehen#this> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kidehen,isnick> .
<http://danbri.org/foaf.rdf#danbri> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/danbri,isnick> .
<http://presbrey.mit.edu/foaf.rdf#presbrey> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/presbrey,isnick> .
<http://dig.csail.mit.edu/People/kennyluck#I> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kennyluck,isnick> .
<http://www.w3.org/People/Berners-Lee/card#i> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/timbl,isnick> .
<http://swordfish.rdfweb.org/people/libby/rdfweb/webwho.xrdf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/libby,isnick> .
<http://tobyinkster.co.uk/#i> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/tobyink,isnick> .
<http://tobyinkster.co.uk/#i> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/tobyink1,isnick> .
<http://simon-reinhardt.de/#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/Shepard,isnick> .
<http://plugin.org.uk/swh.xrdf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/swh,isnick> .
<http://www.cs.univie.ac.at/foaf.php?eid=223#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/besbes,isnick> .
<http://thefigtrees.net/id#lee> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/LeeF,isnick> .
<http://sw-app.org/mic.xhtml#i> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/mhausenblas,isnick> .
<http://myopenlink.net/dataspace/person/tthibodeau#this> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/MacTed,isnick> .
<http://csarven.ca/foaf#sarvencapadisli> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/csarven,isnick> .
<http://buzzword.org.uk/2009/mttlbot/#bot> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/mttlbot,isnick> .
<http://plugin.org.uk/swh.xrdf> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/swh,isnick> .
<http://people.apache.org/~oshani/foaf.rdf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/oshani,isnick> .
<http://bnode.org/grawiki/bengee#self> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/bengee,isnick> .
<http://identi.ca/user/33> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/csarven,isnick> .
<http://kasei.us/about/foaf.xrdf#greg> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kasei,isnick> .
<http://identi.ca/user/9577> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/mattl,isnick> .
<http://blog.reallywow.com/foaf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/lbjay,isnick> .
<http://keithalexander.co.uk/id/me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kwijibo_,isnick> .
<http://keithalexander.co.uk/id/me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/kwijibo,isnick> .
<http://richard.cyganiak.de/foaf.rdf#cygri> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/cygri,isnick> .
<http://foaf.me/melvincarvalho#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/melvster,isnick> .
<http://moustaki.org/foaf.rdf#moustaki> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/yvesr,isnick> .
<http://bblfish.net/people/henry/card#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/bblfish,isnick> .
<http://captsolo.net/semweb/foaf-captsolo.rdf#Uldis_Bojars> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/CaptSolo,isnick> .
<http://mmt.me.uk/foaf.rdf#mischa> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/mischat,isnick> .
<http://www.w3.org/People/Connolly/#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/DanC,isnick> .
<http://tommorris.org/foaf#me> <http://xmlns.com/foaf/0.1/holdsAccount> <irc://192.168.100.27/tommorris,isnick> .
"""

mttlbot_knowledge = [tuple([res[1:-1] for res in t.split(" ")]) 
                     for t in mttlbot_knowledge_nt.split(" .\n") 
                     if t]

def find_person(nick):
    mttlbot_uri = "irc://192.168.100.27/%s,isnick" % nick
    matches = [s for (s,p,o) in mttlbot_knowledge
               if p == FOAF.holdsAccount and o == mttlbot_uri]
    if matches:
        return matches[0]
    else:
        return None
