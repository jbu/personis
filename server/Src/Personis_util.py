#!/usr/bin/env python

import sys,time
import simplejson as json

# utility function to display an object
def showobj(obj, indent):
	print "showobj:"
        for k,v in obj.__dict__.items():
		if ((k == 'time') or (k == 'creation_time')) and (v != None):
			print "%*s %s %s %s (%s)" % (indent, " ", k,"=",time.ctime(v),v)
		else:
			print "%*s %s %s %s" % (indent, " ", k,"=",v)


# utility to print a list of component objects + evidence if printev="yes"
def printcomplist(reslist, printev=None):
	for res in reslist:
		print 'res',res
		print "==================================================================="
		print "Component: ", res.Description
		print "==================================================================="
		showobj(res, 0)
		if res.value_type == "JSON":
			jval = json.loads(res.value)
			print "Value:",jval
		if printev == "yes":
			print "---------------------------------"
			print "Evidence about it"
			print "---------------------------------"
			if res.evidencelist is None:
				print "no evidence"
			else:
				for ev in res.evidencelist:
					if type(ev) == type(dict()):
						showobj(Struct(**ev), 10)
					else:
						showobj(ev, 10)
					print "---------------------------------"

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)

import json as sysjson
import sys
def printjson(jsonobj):
	sysjson.dump(sysjson.loads(jsonobj), sys.stdout, sort_keys=True, indent=4)
	print

