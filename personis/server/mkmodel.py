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

"""
Personis_mkmodel - library functions used to create sets of models.
	Used by the program mkmodel

mkmodel takes a definition of a model (stored in modeldefinitionfile)
and creates a model in modeldirectory for each model 


"""

import sys
from . import base
from . import active
import logging


"""
	Functions for parsing modeldefs. Uses the pyparsing module 

 Modeldef statement grammar:

	name := ID
	flag := '[' QUOTEDSTRING [',' QUOTEDSTRING]* ']'
	value := QUOTEDSTRING | flags
	key_value := name '=' value
	evidence := '[' key_value* ']'
	attribute := key_value | evidence
	path = [ '/' ] name [ '/' name ]*
	context := '@@' path ':' attribute [ ',' attribute ]*
	component := '--' name ':' attribute [ ',' attribute ]*
	view := '==' name ':' path [ ',' path ]

 Example:

@@Location: description="Information about the user's location."
--seenby: type="attribute", value_type="string", description="sensor that has seen this person"
--location: type="attribute", value_type="string", description="Location Component", 
	[evidence_type="explicit", value="Bob"], [evidence_type="explicit", flags= [ "f1", "f2" ], value="blah"]
==fullname: Personal/firstname, Personal/lastname

"""
from .mypyparsing import Word, alphas, alphanums, Literal, ZeroOrMore, quotedString, Forward, removeQuotes, ParseException, Optional, OneOrMore

keyvals = {} # dictionary to hold list of key/value pairs for an element of the  modeldef
attrs = []
paths = [] # list of paths
flags = None
curcontext = ""
themodel = None
Debug = False


def doname(str, loc, toks):
#	print "doname::", toks
	pass

def doflaglist(str, loc, toks):
	global flags
#	print "doflaglist::", toks
	pass
	flags = []
	if (len(toks) < 3) or  (toks[0] != '[') or (toks[-1] != ']'):
		logging.debug("*** bad flag list: %s", toks)
		return
	for i in range(1,len(toks),2):
		flags.append(toks[i])
	ingging.info( "\tflaglist:", flags)

def dokeyval(str, loc, toks):
	global keyvals, flags
#	print "dokeyval::", toks
	if flags != None:
		val = flags
		flags = None
	else:
		val = toks[2]
	if toks[0] in keyvals:
		if type(keyvals[toks[0]]) == type([]):
			keyvals[toks[0]].append(val)
		else:
			keyvals[toks[0]] = [keyvals[toks[0]], val]
	else:
		keyvals[toks[0]] = val
#	print "\tkeyvals::", keyvals

def dokeyval_list(str, loc, toks):
	global keyvals, attrs
#	print "dokeyval_list::", toks
#	print "\tkeyvals", keyvals
	attrs.append(keyvals)
#	print " \tattrs::", attrs
	keyvals = {}


def doevidence(str, loc, toks):
	global attrs
#	print "doevidence:: ", toks
#	print "\t", attrs
	pass

def doevidencelist(str, loc, toks):
#	print "doevidencelist:: ", toks
	pass

def dotells(ev, compid):
	global themodel, curcontext
	evattrs = ["flags", "evidence_type", "source", "owner", "value", "comment", "time", "useby"]
	if not all([a in evattrs for a in ev]):
		logging.debug( "**** evidence attributes %s must be one of %s" % (ev.keys(), repr(evattrs)))
		return 
	if "flags" in ev:
		if type(ev['flags']) != type([]):
			logging.debug( "**** evidence flags %s must be a list" % (ev['flags']))
			return

	if not Debug:
		evobj = base.Evidence(evidence_type="explicit")
		for k,v in v.items():
			evobj.__dict__[k] = v
		themodel.tell(context=curcontext, componentid=compid, evidence=evobj)
		logging.debug(	"""
			evobj = base.Evidence(ev)
			themodel.tell(context=%s, componentid=%s, evidence=%s)
			""" % (curcontext, compid, evobj.__dict__))
	else:
		logging.debug(	"""
			evobj = base.Evidence(ev)
			themodel.tell(context=%s, componentid=%s, evidence=%s)
			""" % (curcontext, compid, ev))
		
		


def docomponent(str, loc, toks):
	global attrs, keyvals, paths, curcontext, themodel, Debug
	if curcontext == "":
		logging.debug( "No context defined for component", toks[1])
	logging.debug( "docomponent:: %s", toks[1])
	logging.debug( " \tattrs:: %s", attrs)
	required = ['type', 'description', 'value_type']
	for x in required:
		if x not in attrs[0]:
			logging.info( "one or more of the required keyvals", required, "not found for %s", toks[1])
			logging.info( attrs[0])
			return
	if not Debug:
		cobj = base.Component(Identifier=toks[1],
			component_type=attrs[0]['type'],
			value_type=attrs[0]['value_type'],
			value_list=attrs[0].get('value'),
			resolver=attrs[0].get('resolver'),
			Description=attrs[0]['description'])
		try:
			res = themodel.mkcomponent(context=curcontext, componentobj=cobj)
		except:
			logging.info( "mkcomponent failed")
		if res != None:
			logging.debug( res)
	logging.debug( """cobj = base.Component(Identifier="%s",
		component_type="%s",
		value_type="%s",
		value_list="%s",
		resolver="%s",
		Description="%s")
		""" % ( toks[1], attrs[0]['type'], attrs[0]['value_type'], attrs[0].get('value'), attrs[0].get('resolver'), attrs[0]['description']))
	if 'rule' in attrs[0]:
		if type(attrs[0]['rule']) != type([]):
			rules = [attrs[0]['rule']]
		for rule in rules:
			if not Debug:
				themodel.subscribe(context=curcontext, view=[toks[1]], subscription=dict(user="bob", password="qwert", statement=rule))
			logging.debug( "\tsub:: %s, %s, %s", curcontext, [toks[1]], dict(user="bob", password="qwert", statement=rule))
	logging.debug( "+++ component created ")
	if len(attrs) > 1: # see if there is some evidence
		for e in attrs[1:]:
			logging.debug( "\tevidence:: %s", e)
			dotells(e, toks[1])
#	del attrs[0]
	attrs = []
	keyvals = {}
	paths = []

def docontext(str, loc, toks):
	global attrs, paths, curcontext, themodel, Debug, keyvals
	logging.debug( "docontext:: %s", toks)
	logging.debug( " \tpaths:: %s", paths)
	logging.debug( " \tattrs:: %s", attrs)
	if len(paths) != 1:
		logging.info( "too many paths", paths)
		raise ParseException("too many paths " + repr(paths))
	curcontext = paths[0]
	logging.debug( "\tcurcontext:: "+ curcontext + repr(curcontext.split('/')))
	if 'description' not in attrs[0]:
		logging.info( "*** description required for ", curcontext)
		raise ParseException("description required for " + repr(curcontext))
	if not Debug:
		cobj = base.Context(Identifier=curcontext.split('/')[-1], Description=attrs[0]['description'])
	logging.debug( "\tbase.Context(Identifier='%s', Description='%s')", curcontext.split('/')[-1], attrs[0]['description'])
	logging.debug( "\t %s", curcontext.split('/')[:-1])
	if not Debug:
		if themodel.mkcontext(curcontext.split('/')[:-1], cobj):
			logging.debug( "+++ context created ok")
		else:
			logging.info( "+++ context creation failed")
	keyvals = {}
	del attrs[0]
	paths = []

def domdef(str, loc, toks):
	#print "domdef::", toks
	logging.debug( "--------------------------------")

def dopath(str, loc, toks):
	global paths
#	print "dopath::", toks
	paths.append(''.join(toks))

def doview(str, loc, toks):
	global paths, curcontext, themodel, Debug
	if curcontext == "":
		logging.info( "No context defined for view %s", toks[1])
		raise ParseException("No context defined for view " + repr(toks[1]))
	if paths == []:
		logging.info( "No paths defined for view %s", toks[1])
		raise ParseException("No paths defined for view " + repr(toks[1]))
	logging.debug( "doview:: %s", toks[1])
	logging.debug( "\t paths:: %s", paths)
	if not Debug:
		vobj = base.View(Identifier=toks[1], component_list=paths)
		themodel.mkview(curcontext, vobj)
	paths = []

#	name := ID
#	attribute := name '=' QUOTEDSTRING
#	path = [ '/' ] name [ '/' name ]
#	context := path ':' attribute [ ',' attribute ]*
#	component := name ':' attribute [ ',' attribute ]*
#	view := name ':' path [ ',' path ]

name = Word(alphanums+"_")
flaglist = Literal('[')+ quotedString.setParseAction(removeQuotes) + ZeroOrMore(Literal(',') + quotedString.setParseAction(removeQuotes)) + Literal(']')
value = quotedString.setParseAction(removeQuotes) | flaglist
keyval = name + Literal("=") + value
keyval_list = keyval + ZeroOrMore(Literal(",") + keyval)
evidence = Literal("[") + keyval_list + Literal("]")
evidencelist = evidence + ZeroOrMore(Literal(",") + evidence)
path = ZeroOrMore(Literal('/')) + name + ZeroOrMore(Literal('/') + name)
context = Literal('@@') + path + Literal(':') + keyval_list
component = Literal('--') + name + Literal(":") + keyval_list + Optional(Literal(',') + evidencelist)
view = Literal('==') + name + Literal(":") + path + ZeroOrMore(Literal(",") + path)
mdef = OneOrMore(context + ZeroOrMore(component) + ZeroOrMore(view)) + Literal('$$')

name.setParseAction(doname)
keyval.setParseAction(dokeyval)
flaglist.setParseAction(doflaglist)
keyval_list.setParseAction(dokeyval_list)
evidence.setParseAction(doevidence)
evidencelist.setParseAction(doevidencelist)
path.setParseAction(dopath)
context.setParseAction(docontext)
component.setParseAction(docomponent)
view.setParseAction(doview)
mdef.setParseAction(domdef)


def domodeldef(mdefstring):
	"""
	function to parse a modeldef statement
	arg is a string containing the mdef statement
	"""
	mdefstring += " $$"
	#print "statement:", mdefstring
	try:
		toks = mdef.parseString(mdefstring)
	except ParseException as err:
		logging.info( '****  Parse Failure  ****')
		logging.info( err.line)
		logging.info( " "*(err.column-1) + "^")
		logging.info( err)

		raise ValueError("parse failed")


"""====================================================================================================================="""
def mkmodel_um(um,lines, debug = 1):
	'''
		Create a model from the model definition in the string "lines"
	'''
	global themodel
	themodel = um
	domodeldef(lines)

#def mkmodel_remote(model=None, mfile=None, modelserver=None, user=None, password=None):
#	server.MkModel(model=model, modelserver=modelserver, user=user, password=password)
#	um = client.Access(model=model, modelserver=modelserver, user=user, password=password)
#	mkmodel_um(um,get_modeldef(mfile))
	

def mkmodel(model=None, mfile=None, modeldir=None, user=None, password=None):
	base.MkModel(model=model, modeldir=modeldir, user=user)
	um = active.Access(model=model, modeldir=modeldir, user=user)
	mkmodel_um(um,get_modeldef(mfile))

def get_modeldef(mfile):
	try:
		mf = open(mfile)
	except:
		logging.info( "cannot open <%s>" % (mfile))
		sys.exit(1)
	lines = ""
	for mline in mf.readlines():
#		mline = mline.strip()
#		if debug:
#			print ">"+mline
		if (len(mline) == 0) or (mline[0] in "#\n"):
			continue
		if mline[:9] == "$include ":
			inclfile = mline[9:].strip()
			logging.debug( "#### include file: %s\n" % (inclfile))
			lines = lines + get_modeldef(inclfile)
			logging.debug( "#### end of include file: %s\n" % (inclfile))
		else:
			lines = lines+mline
	mf.close()
	return lines


if __name__ == '__main__':
	Debug = True
	mdefstring = """
@@Location: description="Information about the user's location."
--seenby: type="attribute", value_type="string", description="sensor that has seen this person"
--location: type="attribute", value_type="string", description="Location Component", 
	[evidence_type="explicit", value="Bob"], [evidence_type="explicit", flags= [ "f1", "f2" ], value="blah"]
"""
	mmdefstring = """
@@Location: description="Information about the users' location."
--seenby: type="attribute", value_type="string", description="sensor that has seen this person"
--location: type="attribute", value_type="string", description="Location", [aa="hhh", bb="kk"]
==fullname: Personal/firstname, Personal/lastname
@@Personal/Work: description="Information about the users work."
--role: description="the users main role in the organisation", type="attribute",
        value_type="enum", value="Academic", value="Postgraduate", value="etc",
	rule="<default!./Personal/email> ~ '*' : NOTIFY 'http://www.somewhere.com/' 'email=' <./Personal/email>",
[aa="hhh", bb="jj"],
[aa="hhh", bb="kk"]
"""
	mmdefstring = """
@@Location: description="Information about the users' location."
--seenby: type="attribute", value_type="string", description="sensor that has seen this person"
--location: type="attribute", value_type="string", description="Location"
@@Work: description="Information about the users work."
--role: description="the users main role in the organisation", type="attribute", 
        value_type="enum", value="Academic", value="Postgraduate", value="etc"

"""
	mmdefstring = get_modeldef("modeldefs/user-test")
	mdefstring = get_modeldef(sys.argv[1])
	logging.debug( "=====================\n",mdefstring,"\n=====================\n")
#	domodeldef(mdefstring)

