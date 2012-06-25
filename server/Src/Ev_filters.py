#!/bin/env python

#
# mixin for Access class containing the evidence filters
#

import time,types,traceback,re
import simplejson as json

from Personis_exceptions import ModelNotFoundError


class Access:
	"""
		Evidence filter mixin for Personis Access

		Contains evidence filter methods that are used before a resolver runs
		To add a new filter, add the method to this class and add an
			entry to the self.evidencefilterlist dictionary
	"""
	def __init__(self):
		self.evidencefilterlist = {"all":self._All_filter, "last1":self.last1_filter, "last10":self.last10_filter, "goal":self.goal_filter, "since_time":self.since_time_filter, "recent_count":self.recent_count_filter}


	def _All_filter(self, elist=None, arguments=None):
		"""
			return all evidence
		"""
		return sorted(elist, key=lambda e: e['creation_time'])
	
	def last1_filter(self, elist=None, arguments=None):
		"""
			return last 1 evidence item
		"""
		elist = sorted(elist, key=lambda e: e['creation_time'])
		return [elist[-1]]
	
	def last10_filter(self, elist=None, arguments=None):
		"""
			return last 10 evidence items
		"""
		elist = sorted(elist, key=lambda e: e['creation_time'])
		return elist[-1:-10]
	
	def goal_filter(self, elist=None, arguments=None):
		"""
			return elements with flag "goal"
		"""
		elist = [e for e in elist if "goal" in e['flags']]
		return sorted(elist, key=lambda e: e['creation_time'])

	def since_time_filter(self, elist=None, arguments=None):
		"""
			return elements with creation_time after arguments["since_time"]
		"""
		try:
			since_time = float(arguments['since_time'])
		except:
			since_time = 0.0
		elist = [e for e in elist if e['creation_time'] > since_time]
		return sorted(elist, key=lambda e: e['creation_time'])

	def recent_count_filter(self, elist=None, arguments=None):
		"""
			return the last arguments["recent_count"] elements
		"""
		elist = sorted(elist, key=lambda e: e['creation_time'])
		return elist[-1:-arguments['recent_count']]

class Evidence_list:
	def __init__(self, elist=None, model=None, componentid=None):
		self.content = elist
		if model != None:
			self.model = model
			self.componentid = componentid
			try:
				self.evdb,self.evdb_fd = shelf_open(model.curcontext+"/.evidence", "r")
			except:
				raise ValueError, "tell: no evidence db for %s"%(model.curcontext)
			if not self.evdb.has_key(self.componentid):
				shelf_close(self.evdb, self.evdb_fd)
				return None # no evidence for this component
			self.totalcount = self.evdb[self.componentid]

	def close(self):
		shelf_close(self.evdb, self.evdb_fd)
		
	def _dbget(index):
		if index < 0:
			index = self.totalcount + index + 1
		return self.evdb.get("%s:%d"%(self.componentid,index))

	def __getitem__(self, index):
		if type(index) == type(1):
			if self.content == None:
				return Evidence_list([self._dbget(index)])
			else:
				if index < 0:
					index = self.totalcount + index + 1
				if (index < len(self.content)) and (index >= 0):
					return Evidence_list([self.content[index]])
				else:
					return Evidence_list([])
		elif type(index) == type(slice):
			step = index.step if index.step != None else 1
			elist = []
			for i in range(index.start, index.stop, step):
				if self.content == None:
					e = self._dbget(index)
					if e != None:
						elist.append(e)
				else:
					if index < 0:
						index = self.totalcount + index + 1
					if (index < len(self.content)) and (index >= 0):
						elist.append(self.content[index])
			return Evidence_list(elist)

