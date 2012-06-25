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
print "Examples that show how app registration works"
print "==================================================================="

um = Personis.Access(model="Alice", user='alice', password='secret')

print ">>>> List the registered apps (should be none):"
apps = um.listapps()
print apps

print ">>>> Try and set permissions on an unregistered app:"
try:
	um.setpermission(context=["Personal"], app="MyHealth", permissions={'ask':True, 'tell':False})
except Exception as e:
	print "setpermission failed with exception : %s\n" % (e)

print ">>>> Register an app"
um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
print ">>>> List the registered apps (should be one):"
apps = um.listapps()
print apps

print ">>>> Set some permissions for the 'MyHealth' app"
um.setpermission(context=["Personal"], app="MyHealth", permissions={'ask':False, 'tell':False})

print ">>>> Show the permissions:"
perms = um.getpermission(context=["Personal"], app="MyHealth")
print "MyHealth:", perms

print ">>>> Try getting permissions for an unregistered app:"
try:
	perms = um.getpermission(context=["Personal"], app="withings")
except Exception as e:
	print "getpermission failed with exception : %s\n" % (e)
else:
	print "withings:", perms

print "+++++++++++++++++++++++++++++++++++++++++++++++++++++++"
print ">>>> Now testing permissions"
print
print ">>>> Tell full name as owner"
ev = Personis_base.Evidence(source="demoex2", evidence_type="explicit", value="Alice")
um.tell(context=["Personal"], componentid='firstname', evidence=ev)
ev = Personis_base.Evidence(source="demoex2", evidence_type="explicit", value="Smith")
um.tell(context=["Personal"], componentid='lastname', evidence=ev)

print ">>>> Ask for Alice's fullname as owner (should work)"
reslist = um.ask(context=["Personal"], view='fullname')
print reslist[0].value, reslist[1].value

um = None
print ">>>> Access Alice's model as an unregistered App (should NOT work):"
try:
	um = Personis.Access(model="Alice",  user='withings', password='secret')
except Exception as e:
	print "Access failed with exception : %s\n" % (e)
else:
	print "**** access worked when it should have failed"

um = None
print ">>>> Access Alice's model as a registered App:"
try:
	um = Personis.Access(model="Alice", user='MyHealth', password='pass9')
except Exception as e:
	print "Access failed with exception : %s\n" % (e)
else:
	print "++++ access successful"

print ">>>> Ask for Alice's fullname as app 'MyHealth' (should NOT work)"
try:
	reslist = um.ask(context=["Personal"], view='fullname')
	print reslist[0].value, reslist[1].value
except Exception as e:
	print "ask failed with exception : %s\n" % (e)
else:
	print "**** ask worked when it should have failed"

print ">>>> Set ask permission for the 'MyHealth' app"
um = None
um = Personis.Access(model="Alice", user='alice', password='secret')
um.setpermission(context=["Personal"], app="MyHealth", permissions={'ask':True, 'tell':False})


um = None
um = Personis.Access(model="Alice", user='MyHealth', password='pass9')
print ">>>> Ask for Alice's fullname as app 'MyHealth' (should work now)"
try:
	reslist = um.ask(context=["Personal"], view='fullname')
	print reslist[0].value, reslist[1].value
except Exception as e:
	print "ask failed with exception : %s\n" % (e)
else:
	print "++++ ask successful"

print ">>>> Now try and tell a new value for first name (should NOT work)"
ev = Personis_base.Evidence(source="MyHealth", evidence_type="explicit", value="Fred")
try:
	um.tell(context=["Personal"], componentid='firstname', evidence=ev)
except Exception as e:
	print "tell failed with exception : %s\n" % (e)
else:
	print "++++ tell successful"

print ">>>> Delete the 'MyHealth' app while NOT accessing as owner"
try:
        um.deleteapp(app="MyHealth")
except Exception as e:
        print "deleteapp failed with exception : %s\n" % (e)
else:
        print "FAILED: deleteapp should not be able to delete app when not owner"

um = None
um = Personis.Access(model="Alice", user='alice', password='secret')
print ">>>> Delete the 'MyHealth' app while accessing as owner"
try:
        um.deleteapp(app="MyHealth")
except Exception as e:
        print "deleteapp failed with exception : %s\n" % (e)
else:
        print "deleteapp succeeded"
print ">>>> List the registered apps (should be none):"
apps = um.listapps()
print apps

