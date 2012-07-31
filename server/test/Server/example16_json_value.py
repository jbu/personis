#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist
import json


print ">>>> add a JSON encoded value to a component"
fullname = {'firstname':'Judy', 'lastname':'Kay'}
um = Personis.Access(model="Alice", user='alice', password='secret')
# create a piece of evidence with demoex2 as source and json encoded value
ev = Personis_base.Evidence(source="demoex2", evidence_type="explicit", value=json.dumps(fullname))
um.tell(context=["People"], componentid='fullname', evidence=ev)

print "==================================================================="
print ">>>> Now check the evidence list "
reslist = um.ask(context=["People"], view=['fullname'])
printcomplist(reslist, printev = "yes")

