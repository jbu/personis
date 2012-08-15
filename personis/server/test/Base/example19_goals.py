#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist, showobj

print("Testing goals")
print("\tcreate a new component")
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
cobj = Personis_base.Component(Identifier="fitness", component_type="goal", Description="My overall fitness", goals=[['Personal', 'Health', 'weight']], value_type="number")
showobj(cobj, 1)

res = um.mkcomponent(context=["Personal"], componentobj=cobj)
print(repr(res))

print("\t show this component in the Personal context")
ev = Personis_base.Evidence(evidence_type="explicit", value=17)
um.tell(context=["Personal"], componentid='fitness', evidence=ev)
reslist = um.ask(context=["Personal"], view=['fitness'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")

goals = reslist[0].goals
print("Old goals are:", goals)
print("\tadding a goal")
goals.append(["Personal", "Health", "steps"])
um.set_goals(context=["Personal"], componentid='fitness', goals=goals)

reslist = um.ask(context=["Personal"], view=['fitness'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")


