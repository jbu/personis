#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import showobj, printcomplist

print "==================================================================="
print "examples that just print parts of the model"

um = Personis.Access(model="Alice", user='alice', password="secret")

print "==================================================================="
print ">>>> 1. ask for Alice's fullname"
reslist = um.ask(context=["Personal"], view='fullname')
printcomplist(reslist, printev = "yes")

print "==================================================================="
print ">>>> 2. ask for Alice's first then last name"

res = um.ask(context=["Personal"], view=['firstname', 'lastname'])
printcomplist(res, printev = "yes")

print "==================================================================="
print ">>>> 3. ask for Alice's gender"
res = um.ask(context=["Personal"], view=['gender'])
printcomplist(res, printev = "yes")

print "==================================================================="
print ">>>> 4. ask for Alice's artist preferences"

reslist = um.ask(context=["Preferences", "Music", "Jazz", "Artists"], view=['Miles_Davis'])
printcomplist(reslist, printev = "yes")

print "==================================================================="
print ">>>> 5. ask for all the components in the Personal context - 5 of them"

reslist = um.ask(context=["Personal"])
printcomplist(reslist, printev = "yes")
