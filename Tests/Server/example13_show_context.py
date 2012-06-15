#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import showobj, printcomplist

def printAskContext( info ):
	(cobjlist, contexts, theviews, thesubs) = info
	printcomplist(cobjlist, printev = "yes")
	print "Contexts: %s" % str(contexts)
	print "Views: %s" % str(theviews)
	print "Subscriptions: %s" % str(thesubs)
		
print "==================================================================="
print "Examples that show how the showcontext call works"
print "==================================================================="

um = Personis.Access(model="Alice", user='alice', password='secret')

print ">>>> 1. Show the root context"
info = um.ask(context=[""], showcontexts=True)
printAskContext (info)

print ">>>> 2. Show the Personal context"
info = um.ask(context=["Personal"], showcontexts=True)
printAskContext (info)
