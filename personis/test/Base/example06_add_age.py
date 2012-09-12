#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist, showobj

# create a new component
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
cobj = Personis_base.Component(Identifier="age", component_type="attribute", Description="age", goals=[['Personal', 'Health', 'weight']], value_type="number")
showobj(cobj, 1)

res = um.mkcomponent(context=["Personal"], componentobj=cobj)
print(repr(res))

# show this age in the Personal context
ev = Personis_base.Evidence(evidence_type="explicit", value=17)
um.tell(context=["Personal"], componentid='age', evidence=ev)
reslist = um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")
