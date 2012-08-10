#!/usr/bin/env python

import Personis_base
from Personis_util import showobj, printcomplist

def printAskContext( info ):
	(cobjlist, contexts, theviews, thesubs) = info
	printcomplist(cobjlist, printev = "yes")
	print "Contexts: %s" % str(contexts)
	print "Views: %s" % str(theviews)
	print "Subscriptions: %s" % str(thesubs)
		
print "==================================================================="
print "Simple example showing how permissions work"
print "==================================================================="

um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')

print "Register an app"
appdetails = um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
print "Registered ok: ", appdetails
print "List the registered apps (should be one):"
apps = um.listapps()
print apps

print "Set some permissions for the 'MyHealth' app"
um.setpermission(context=["Personal"], app="MyHealth", permissions={'ask':True, 'tell':False})

print "Show the permissions"
perms = um.getpermission(context=["Personal"], app="MyHealth")
print "MyHealth:", perms
print "Ask for permission for an unregistered app"
try:
	perms = um.getpermission(context=["Personal"], app="withings")
	print "withings:", perms
except Exception as e:
	print "getpermission failed with exception: %s\n" % (e)

print "Delete the 'MyHealth' app while accessing as owner"
try:
        um.deleteapp(app="MyHealth")
except Exception as e:
        print "deleteapp failed with exception : %s\n" % (e)
else:
        print "deleteapp succeeded"
print "List the registered apps (should be none):"
apps = um.listapps()
print apps

