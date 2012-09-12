#!/usr/bin/env python

import Personis_base
from Personis_util import showobj, printcomplist

um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')

print("before deleting the email view")
try:
	reslist= um.ask(context=["Personal"], view = 'email_details', resolver={'evidence_filter':"all"})
	printcomplist(reslist)
except:
	print("ask failed")

try:
	um.delview(context=["Personal"], viewid = "email_details")
except:
	print("failed attempt to delete view")
