#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist
import json


print "add a JSON encoded value to a component"
fullname = {'firstname':'Alice', 'lastname':'Smith'}
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
# create a piece of evidence with json encoded value
ev = Personis_base.Evidence(evidence_type="explicit", value=json.dumps(fullname))
um.tell(context=["People"], componentid='fullname', evidence=ev)

print "==================================================================="
print "Now check the evidence list "
reslist = um.ask(context=["People"], view=['fullname'])
printcomplist(reslist, printev = "yes")

