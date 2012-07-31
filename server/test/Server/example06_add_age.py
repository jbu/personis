#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist, showobj

print ">>>> create an 'age' component"
um = Personis.Access(model="Alice", user='alice', password='secret')
cobj = Personis_base.Component(Identifier="age", component_type="attribute", Description="age", value_type="number")
showobj(cobj, 1)

res = um.mkcomponent(context=["Personal"], componentobj=cobj)
print `res`

print ">>>> show the age component in the Personal context"
ev = Personis_base.Evidence(source="example 6", evidence_type="explicit", value=17)
um.tell(context=["Personal"], componentid='age', evidence=ev)
reslist = um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")
