#!/bin/env python2.4

"""
	Functions for handling subscriptions

	Uses the pyparsing module to parse and execute the subscription statement.
	
	Run as a standalone program for testing.


 Subscription statement grammar:

	resolvername := ID
	evidencetype := ID
	componentval := '<' [ resolvername '!' ] component '>'
	componentname := ID | componentval
	modelname := '.' | componentname
	component := modelname [ '/' componentname ]*
	cronspec := '[' QUOTEDSTRING ']'
	item := component | QUOTEDSTRING
	patternmatch := item '~' item
	tell := 'TELL' item ',' evidencetype ':' item
	tellchanged := 'TELLCHANGED' item ',' evidencetype ':' item
	notify := 'NOTIFY' item [item]*
	action := tell | tellchanged | notify
	statement := [ cronspec ] patternmatch ':' action

 Note:
	a cronspec string is similar to a crontab entry: "minute hour day_of_month month day_of_week"

 Examples:

 <froomBT/seen> ~ '.*' : TELL <froomBT/seen>/location, <froomBT/location>"
 <froomBT/seen> ~ '.*' : NOTIFY 'http://www/qqq.cgi'"
 <froomBT/seen> ~ '.*' : TELL bob/personal/location, explicit:<froomBT/location>
 <bob/personal/location> ~ '.*' : NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
 ["*/15 * * * *"] <bob/personal/location> ~ '.*' : NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
 <default!bob/personal/location> ~ '.*' : NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
 <default!bob/personal/location> ~ '.*' : NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
 <bobPhone/seenby> ~ '.*' : TELL bobPhone/location, explicit:<<bobPhone/seenby>/location>
 <default!./personal/location> ~ '.*' : NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'location=' <./personal/location>  '&name=' <./personal/firstname>

"""
#import Personis_server
import Personis_base
import re
from mypyparsing import Word, alphas, Literal, ZeroOrMore, quotedString, Forward, removeQuotes, ParseException, Optional, OneOrMore


def askval(str, loc, toks):
	if toks[2] == '!': 
		resolver = toks[1]
		del toks[1:3]
	else:
		resolver = "default"
	model = toks[1]
	if model == '.': model = defaultmodel
	context = [x for x in toks[2:-3] if x != '/']
	componentid = toks[-2]
	print "AskVal -> resolver: %s, model: %s, context: %s, componentid:%s" % (resolver, model, context, componentid)
	if model != defaultmodel:
		global Personis
		import Personis as pmdns
		try:
			um = pmdns.Access(model=model, user=user, password=password)
			reslist = um.ask(context=context, view=[componentid], resolver=resolver)
		except:
			print "ask failed"
			return "-no model-"
	else:
		reslist = currentum.ask(context=context, view=[componentid], resolver=resolver)
	print "result: ", reslist[0].value
	if reslist[0].value == None:
		return ""
	else:
		return reslist[0].value

def domatch(str, loc, toks):
	print "TOKS:", toks
	if re.compile(toks[2]).match(toks[0]):
		return "-match-"
	else:
		raise ParseException, (str, loc, "match failed",0)
		
def dotellchanged(str, loc, toks):
	return dotell_body(str, loc, toks, changed_only=True)

def dotell(str, loc, toks):
	return dotell_body(str, loc, toks)

def dotell_body(str, loc, toks,changed_only=False):
	model = toks[1]
	if model == '.': model = defaultmodel
	context = [x for x in toks[2:-6] if x != '/']
	componentid = toks[-5]
	evidence_type = toks[-3]
	newval = toks[-1]
	
	print "Tell %s/%s/%s, %s:%s" % (model, context, componentid, evidence_type, newval)
	try:
		if model!=defaultmodel:
			global Personis
			import Personis as pmdns
			um = pmdns.Access(model=model, user=user, password=password)
			if changed_only:
				comp = um.ask(context=context, view=[componentid], resolver='default')[0]
				if comp.value == newval:
					return True # don't actually need to do the tell
			um.tell(context=context, componentid=componentid,
				evidence=Personis_base.Evidence(evidence_type=evidence_type, value=newval))
		else:
			if changed_only:
				comp = currentum.ask(context=context, view=[componentid], resolver='default')[0]
				if comp.value == newval:
					return True # don't actually need to do the tell
			currentum.tell(context=context, componentid=componentid,
				evidence=Personis_base.Evidence(evidence_type=evidence_type, value=newval))

	except:
		print 'tell failed'
		raise ParseException, (str, loc, "tell failed",0)
	return True

def donotify(str, loc, toks):
	#print "donotify::", toks
	url = "".join(toks[1:])
	import urllib
	print "Notify", url
	f = urllib.urlopen(url)
	print f.readlines()
	f.close()
	return

component = Forward()
componentval = Literal("<")+Optional(Word(alphas) + Literal('!'))+component+Literal(">")
componentval.setParseAction(askval)
componentname = Word(alphas) | componentval
modelname = Literal('.') | componentname
component << modelname + ZeroOrMore(Literal('/') + componentname)
item = component | quotedString.setParseAction(removeQuotes)
cronspec = Literal('[') + quotedString.setParseAction(removeQuotes) + Literal(']')
patternmatch = item + Literal('~') + item 
patternmatch.setParseAction(domatch)
tell = Literal('TELL') + item + Literal(',') + item + Literal(':') + item
tell.setParseAction(dotell)
tellchanged = Literal('TELLCHANGED') + item + Literal(',') + item + Literal(':') + item
tellchanged.setParseAction(dotellchanged)
notify = Literal('NOTIFY') + OneOrMore(item)
notify.setParseAction(donotify)
action = tell | notify | tellchanged
subgrammar = Optional(cronspec) + patternmatch + Literal(':') + action

user = None
password = None
statement = ""

def dosub(sub, um):
	"""
	function to parse and execute a subscription statement
	takes one dictionary argument containing:
	user, password to be used in Access'ing the model and
	statement, a string containing the subscription statement
	"""
	global currentum
	currentum = um
	global defaultmodel
	defaultmodel = um.modelname
	user = sub['user']
	password = sub.get('password')
	statement = sub['statement']
	print "default model:", defaultmodel
	print "statement:", statement
	try:
		toks = subgrammar.parseString(statement)
	except Exception as err:
		print "parse failed [[%s]]" % (`err`)
	else:
		return True



class Dummyum:
	def __init__(self, name):
		self.modelname = name
	
if __name__ == '__main__':
	testsub = "<froomBT/seen> ~ '.*' : TELL <froomBT/seen>/location, <froomBT/location>"
	testsub = "<froomBT/seen> ~ '.*' : NOTIFY 'http://www/qqq.cgi'"
	testsub = """
 <froomBT/seen> ~ '.*' :
	 TELL bob/personal/location, explicit:<froomBT/location>
"""
	testsub = """
 <bob/personal/location> ~ '.*' :
	 NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
"""
	testsub = """
 <default!bob/personal/location> ~ '.*' :
	 NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
"""
	testsub = """
 <default!bob/personal/location> ~ '.*' :
	 NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi'
"""
	testsub = """
<bobPhone/seenby> ~ '.*' : TELL bobPhone/location, explicit:<<bobPhone/seenby>/location>
"""
	testsub = """
 ["*/15 * * * *"] <default!./personal/location> ~ '.*' :
	 NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'location=' <./personal/location>  '&name=' <./personal/firstname>
"""
	testsub = """
 <default!./personal/location> ~ '.*' :
	 NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'location=' <./personal/location>  '&name=' <./personal/firstname>
"""
	print testsub
	dosub({'user':'bob', 'password':'qwert', 'statement':testsub}, Dummyum("bob"))
