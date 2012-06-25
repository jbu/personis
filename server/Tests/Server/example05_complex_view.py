#!/usr/bin/env python

import Personis
import Personis_base
from Personis_util import printcomplist

print ">>>> ask for the components in a more complex view of a preference and Alice's first name"
# get component objects for a more complex view
# in this case the first component is "Miles_Davis" in 
# the nominated context, the second component is 
# "firstname" in the "Personal" context
um = Personis.Access(model="Alice", user='alice', password='secret')
reslist = um.ask(context=["Preferences", "Music", "Jazz", "Artists"], 
	view=['Miles_Davis', ['Personal', 'firstname']], resolver={'evidence_filter':"all"})

print "==================================================================="
print ">>>> Now check the evidence list for that view"
printcomplist(reslist, printev = "yes")

res2 = um.ask(context=["Personal"], view=["firstname"], resolver={'evidence_filter':"all"})
print "==================================================================="
printcomplist(res2, printev = "yes")

