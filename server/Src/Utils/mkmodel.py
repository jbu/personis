#!/usr/bin/env python

"""

mkmodel - a program to create a set of models
usage: mkmodel modeldefinitionfile modeldirectory modelname modelname ...

mkmodel takes a definition of a model (stored in modeldefinitionfile)
and creates a model in modeldirectory for each model 

see external documentation for the definition of the modeldef language

"""

import sys
from Personis_mkmodel import *


def doit():
	if len(sys.argv) < 4 or '--modelserver'== sys.argv[-1]:
		print "usage: mkmodel modelfile modeldir model-name ...."
		print "or: mkmodel --modelserver modelservername:port modelfile model-name ...."
		sys.exit(0)

	modelserver = None
	if len(sys.argv) > 4 and '--modelserver' in sys.argv[:-1]:
		ind = sys.argv.index('--modelserver')
		modelserver = sys.argv[ind+1]
		del sys.argv[ind+1]
		del sys.argv[ind]
		for m in sys.argv[2:]:
			mname,user,password = m.split(":")
			mkmodel_remote(model=mname, mfile=sys.argv[1], modelserver=modelserver, user=user, password=password)
	else:
		for m in sys.argv[3:]:
			mname,user,password = m.split(":")
			print mname, sys.argv[1], sys.argv[2], user, password
			mkmodel(model=mname, mfile=sys.argv[1], modeldir=sys.argv[2], user=user, password=password)


if __name__ == '__main__':
	doit()
	
