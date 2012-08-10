#!/usr/bin/env python

import Personis_base 
from Personis_util import showobj, printcomplist


um = Personis_base.Access(model="Alice", modeldir='Tests/Models', user='alice', password='secret')


for i in range(100000):
	res = um.ask(context=["Personal"], view=['gender'])
