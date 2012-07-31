#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist

# add some evidence to a component in the music preferences
print "add a preference for Alice for Miles_Davis"
ev = Personis_base.Evidence(evidence_type="explicit", value=4)
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
um.tell(context=["Preferences", "Music","Jazz","Artists"], componentid='Miles_Davis', evidence=ev)

print "==================================================================="
print "Now check the evidence list for that preference"
reslist = um.ask(context=["Preferences", "Music", "Jazz", "Artists"], view=['Miles_Davis'], resolver={'evidence_filter':"all"})
printcomplist(reslist, printev = "yes")

