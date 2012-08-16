#!/usr/bin/env python

import Personis_base
from Personis_util import printcomplist, showobj

# create a new context
um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')

print("creating context 'Deltest' in context 'Personal'")
cobj = Personis_base.Context(Identifier="Deltest", Description="testing context deletion")
um.mkcontext(context=["Personal"], contextobj=cobj)

print("getting context information:")
print(("Info with size:", um.getcontext(context=["Personal"], getsize=True)))
print((um.getcontext(context=["Personal", "Deltest"])))

print("now deleting it")
if um.delcontext(context=["Personal", "Deltest"]):
	print("ok")
else:
	print("fail")

print("check for tgz file in Models directory")
