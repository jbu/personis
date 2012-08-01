#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import showobj, printcomplist

print ">>>> create a new view in a given context"
um = Personis.Access(model='Alice', user='alice', password='secret')
vobj = Personis_base.View(Identifier="email_details", component_list=["firstname", "lastname", "email"])

print ">>>> view object with Alice's email details, names and email address"
showobj(vobj, 1)

um.mkview(context=["Personal"], viewobj=vobj)

reslist= um.ask(context=["Personal"], view = 'email_details', resolver={'evidence_filter':"all"})
printcomplist(reslist)
