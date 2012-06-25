#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import showobj, printcomplist

um = Personis.Access(model="Alice", user='alice', password='secret')

print ">>>> delete the email view"
try:
	reslist= um.ask(context=["Personal"], view = 'email_details', resolver={'evidence_filter':"all"})
	printcomplist(reslist)
except:
	print "ask failed"

try:
	um.delview(context=["Personal"], viewid = "email_details")
except:
	print ">>>> failed attempt to delete view"
