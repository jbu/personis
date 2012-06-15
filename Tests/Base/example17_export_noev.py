#!/usr/bin/env python

import sys
import Personis
import Personis_base
import Personis_a
from Personis_util import printcomplist, printjson

# export a model sub tree to JSON

um = Personis_a.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')
modeljson = um.export_model(["Personal"], resolver="default")
#modeljson = um.export_model(["Personal"])
printjson(modeljson)

um.import_model(context=["Temp"], partial_model=modeljson)
#um.import_model(partial_model=modeljson)

modeljson = um.export_model(["Temp"])
printjson(modeljson)
