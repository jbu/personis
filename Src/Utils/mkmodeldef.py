#!/usr/bin/env python

"""

dumpmodel - a program to dump a model in Modeldef form
	takes a text file containing a json representation of a model and converts it to modeldef format
usage: mkmodeldef json-model-file

see external documentation for the definition of the modeldef language

"""

import sys
import json

def doit():
	if len(sys.argv) != 2:
		print "usage: mkmodeldef json-model-file ...."
		sys.exit(0)
	partial_model = "".join(open(sys.argv[1]).readlines())
	dump_model(partial_model=partial_model)

def printlist(v):
	print "[",
	first = True
	for e in v:
		if first == True:
			first = False
		else:
			print ", ",
		print '"%s"' % (e),
	print "]",

def dump_model(context=[], partial_model=None):
	"""
	arguments:
		context - context to import partial model to
			if None, use root of model
		partial_model - string containing JSON representation of model dictionary
			OR
			a dictionary with elements:
				contextinfo - Description, Identifier, perms, resolver
				contexts - sub contexts
				components
				views
				subs
	"""
		
	#print "partial_model:: ", partial_model
	if partial_model == None:
		return
	if type(partial_model) == type(""):
		newmodel = json.loads(partial_model)
	else:
		newmodel = partial_model
	cinfo = newmodel['contextinfo']
	newcontext = context+[cinfo['Identifier']]
	print "\n\n@@%s:" % ("/".join(newcontext))
	for compname, comp in newmodel['components'].items():
		print "\n--%s: " % (compname),
		first = True
		for k,v in comp.items():
			if (k != "evidencelist") and (k != "Identifier"):
				if first == True:
					first = False
				else:
					print ", ",
				print '%s='% (k),
				if type(v) == type([]):
					printlist(v)
				else:
					print '"%s"' % (v),
		if compname in newmodel['subs']:
			for subname, sub in newmodel['subs'][compname].items():
				print ', rule="%s"' % (sub['statement'])
		comp["evidencelist"].reverse()
		if comp["evidencelist"] != []:
			print ","
		for ev in comp["evidencelist"]:
			print "[",
			first = True
			for k,v in ev.items():
				if k == "objectType":
					continue
				if first == True:
					first = False
				else:
					print ", ",
				print '%s='% (k),
				if type(v) == type([]):
					printlist(v)
				else:
					print '"%s"' % (v),
			print "]"
	for viewname, view in newmodel['views'].items():
		print "==%s:" % (viewname),
		first = True
		for k,v in view.items():
			if first == True:
				first = False
			else:
				print ", ",
			print '%s='% (k),
			if type(v) == type([]):
				printlist(v)
			else:
				print '"%s"' % (v),
	if newmodel['contexts'] != None:
		for contextname, cont in newmodel['contexts'].items():
			#print "\n\n>>CONTEXT", contextname, cont
			dump_model(context=newcontext, partial_model=cont)
	
	return

if __name__ == '__main__':
	doit()

