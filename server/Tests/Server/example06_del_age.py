#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist, showobj

print ">>>> delete a component"
um = Personis.Access(model="Alice", user='alice', password='secret')

print "before attempting to delete age"
reslist = um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")

print "after attempting to delete age"
resd = um.delcomponent(context=["Personal"], componentid = "age")
print `resd`

