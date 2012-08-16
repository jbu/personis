#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist, showobj

# create a new component
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')

print("before attempting to delete age")
reslist = um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")

print("after attempting to delete age")
resd = um.delcomponent(context=["Personal"], componentid = "age")
print((repr(resd)))

