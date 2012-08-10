#!/usr/bin/env python

# The Personis system is copyright 2000-2012 University of Sydney
#       Bob.Kummerfeld@Sydney.edu.au

# This file is part of Personis.

# Personis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Personis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Personis.  If not, see <http://www.gnu.org/licenses/>.

import sys,time
import json

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

import sys
def printjson(jsonobj):
	json.dump(json.loads(jsonobj), sys.stdout, sort_keys=True, indent=4)
	print

