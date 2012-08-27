
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

from multiprocessing import Process, Queue
import time
from . import subscription
from . import base as pmdns
import logging

cronq = None # message q

crondb = {} # rule database
crondblen = 0

def time_in_spec(t, spec):
	return (t.tm_min in spec['minset']) and\
		(t.tm_hour in spec['hourset']) and\
		(t.tm_mday in spec['domset']) and\
		(t.tm_mon in spec['monthset']) and\
		(t.tm_wday in spec['dowset'])

def chkspec(t,spec,orig):
	full = dict(minset=set(range(60)), hourset = set(range(24)), domset = set(range(31)), monthset = set(range(12)), dowset = set(range(7)))
	now = dict(minset=set([t.tm_min]), hourset = set([t.tm_hour]), domset = set([t.tm_mday]), monthset = set([t.tm_mon]), dowset = set([t.tm_wday]))
	print "full = ",full
	print "spec = ",spec
	for s in ['minset','hourset','domset','monthset','dowset']:
		if spec[s] != full[s]:
			print "%s : %s" % (s, spec[s])
			if now[s].issubset(spec[s]):
				print ">>%s : %s" % (s, orig[s].difference(now[s]))
				speccopy = spec.copy()
				speccopy[s] = orig[s].difference(now[s])
				return speccopy
	return []

def checksub(modeldir, m):
	sub = m['subscription']
	try:	
		um = pmdns.Access(modeldir=modeldir, model=sub['modelname'], user=sub['user'], password=sub['password'])
	except:
		print "Access failed", sub
		return
	print "Access OK", sub
	try:
		subscription.dosub(sub,um)
	except:
		print "dosub failed"
		return
	print "dosub ok"
	

def cronserver(q, modeldir):
	global crondb, crondblen
	while True:
		try:
			m = q.get(True, 60) # block for 60 seconds at most
		except :
			m = None
		# check cron rules every 60 seconds at least
		# print "======", time.ctime()
		if m == None:
			for i in range(crondblen):
				Doco = '''
--------------------------------------------------------------------------------------------------------
initially newspec is []
newspec is either [] or cronspec minus the previous times if those times are immediately adjacent
eg if cronspec minutes were 3,4,6,7 then 
	at time 3 rule fires and newspec will become 4,6,7 
	at time 4 rule fires and newspec will become 3,6,7 
	at time 5 newspec will become 3,4,6,7
	at time 6 rule fires and newspec will become 3,4,7 
	at time 7 rule fires and newspec will become 3,4,6
	at time 8 newspec will become 3,4,6,7

if newspec is [] 
	if cronspec in current time
		fire rule
		set newspec to (cronspec - current time)
		
else
	if newspec in current time
		fire rule
		set newspec to (newspec - current time (for all parts))
		
		
--------------------------------------------------------------------------------------------------------
'''
				cronspec = crondb[i]['cronspec']
				newspec = crondb[i]['newspec']
				tnow = time.localtime()
				if newspec == []:
					if time_in_spec(tnow, cronspec):
						newspec = chkspec(tnow, cronspec, cronspec)
						print "=== FIRED cronspec ===", time.ctime(), newspec
						checksub(modeldir, crondb[i])
						#print i,":",crondb[i]
				else:
					if time_in_spec(tnow, newspec):
						newspec = chkspec(tnow, newspec, cronspec)
						print "=== FIRED newspec ===", time.ctime(), newspec
						checksub(modeldir, crondb[i])
						#print i,":",crondb[i]
				crondb[i]['newspec'] = newspec
			continue
		if m["op"] == "quit":
			break
		elif m["op"] == "put":
			cspec = m['subscription']['statement']
			(cspec,therest) = cspec.split("]",1)
			cspec = cspec.strip()[1:].strip().strip(''''"''')
			(min, hour, dom, month, dow) = cspec.split(" ", 4)
			#print "cspec = <%s>" % (cspec)
			#print "min = %s, hour = %s, dom = %s, month = %s, dow = %s" % (min,hour,dom,month,dow)
			minset = crontab_parser(60).parse(min)
			hourset = crontab_parser(24).parse(hour)
			domset = crontab_parser(31).parse(dom)
			monthset = crontab_parser(12).parse(month)
			dowset = crontab_parser(7).parse(dow)
			#print "minset = %s, hourset = %s, domset = %s, monthset = %s, dowset = %s" % (minset,hourset,domset,monthset,dowset)
			m['cronspec'] = dict(minset=minset, hourset=hourset, domset=domset, monthset=monthset, dowset=dowset)
			m['newspec'] = []
			crondb[crondblen] = m
			print "put:", m
			crondblen += 1


def weekday(dayname):
	return ["sun", "mon", "tue", "wed", "thu", "fri", "sat"].index(dayname[0:3].tolower())

class crontab_parser(object):
    """Parser for crontab expressions. Any expression of the form 'groups'
    (see BNF grammar below) is accepted and expanded to a set of numbers.
    These numbers represent the units of time that the crontab needs to
    run on::
 
        digit   :: '0'..'9'
        dow     :: 'a'..'z'
        number  :: digit+ | dow+
        steps   :: number
        range   :: number ( '-' number ) ?
        numspec :: '*' | range
        expr    :: numspec ( '/' steps ) ?
        groups  :: expr ( ',' expr ) *
 
    The parser is a general purpose one, useful for parsing hours, minutes and
    day_of_week expressions.  Example usage::
 
        >>> minutes = crontab_parser(60).parse("*/15")
        [0, 15, 30, 45]
        >>> hours = crontab_parser(24).parse("*/4")
        [0, 4, 8, 12, 16, 20]
        >>> day_of_week = crontab_parser(7).parse("*")
        [0, 1, 2, 3, 4, 5, 6]
 
    """
    ParseException = "ParseException"
 
    _range = r'(\w+?)-(\w+)'
    _steps = r'/(\w+)?'
    _star = r'\*'
 
    def __init__(self, max_=60):
	import re
        self.max_ = max_
        self.pats = (
                (re.compile(self._range + self._steps), self._range_steps),
                (re.compile(self._range), self._expand_range),
                (re.compile(self._star + self._steps), self._star_steps),
                (re.compile('^' + self._star + '$'), self._expand_star))
 
    def parse(self, spec):
        acc = set()
        for part in spec.split(','):
            if not part:
                raise self.ParseException("empty part")
            acc |= set(self._parse_part(part))
        return acc
 
    def _parse_part(self, part):
        for regex, handler in self.pats:
            m = regex.match(part)
            if m:
                return handler(m.groups())
        return self._expand_range((part, ))
 
    def _expand_range(self, toks):
        fr = self._expand_number(toks[0])
        if len(toks) > 1:
            to = self._expand_number(toks[1])
            return list(range(fr, min(to + 1, self.max_ + 1)))
        return [fr]
 
    def _range_steps(self, toks):
        if len(toks) != 3 or not toks[2]:
            raise self.ParseException("empty filter")
        return self._filter_steps(self._expand_range(toks[:2]), int(toks[2]))
 
    def _star_steps(self, toks):
        if not toks or not toks[0]:
            raise self.ParseException("empty filter")
        return self._filter_steps(self._expand_star(), int(toks[0]))
 
    def _filter_steps(self, numbers, steps):
        return [n for n in numbers if n % steps == 0]
 
    def _expand_star(self, *args):
        return list(range(self.max_))
 
    def _expand_number(self, s):
        if isinstance(s, basestring) and s[0] == '-':
            raise self.ParseException("negative numbers not supported")
        try:
            i = int(s)
        except ValueError:
            try:
                i = weekday(s)
            except KeyError:
                raise ValueError("Invalid weekday literal '%s'." % s)
        return i

