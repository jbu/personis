#!/usr/bin/env python

import sys
import Personis
import Personis_base
import Personis_a
from Personis_util import printcomplist, printjson

# import a model sub tree from JSON

um = Personis_a.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
modelfile = "exprev"
print "importing:", modelfile
modeljson = open(modelfile).read()
um.import_model(partial_model=modeljson)

