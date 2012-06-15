#!/bin/env python

#
# mixin for Access class containing the resolvers
#

import time,types,traceback,re
import simplejson as json

from Personis_exceptions import ModelNotFoundError


class Access:
	"""
		Resolver mixin for Personis Access

		Contains resolver methods that can be specified on an "ask" operation
		To add a new resolver, add the method to this class and add an
			entry to the self.resolverlist dictionary
	"""
	def __init__(self):
		self.resolverlist = {"default":self._DefaultResolver, "goal":self.GoalResolver, "recent":self.RecentResolver}

	
	def _DefaultResolver(self, model=None, component=None, context=None, resolver_args=None):
		"""	resolver function used if none specified
			sets component value to the value from the 
			last piece of given, non-goal evidence
		"""
		ev, evcount = component.getevidence(model=model, context=context)
		while evcount > 0:
			if ev != None:
				if not ("goal" in ev.flags):
					component.value = ev.value
					break
				else:
					ev, evcount = component.getevidence(model=model, context=context, count=evcount-1)
					continue
			else:
				component.value = None
				break
		if evcount == 0:
			component.value = None
		component.evidencelist = component.filterevidence(model=self, context=context, resolver_args=resolver_args)
		return component

	def GoalResolver(self, model=None, component=None, context=None, resolver_args=None):
		"""	resolver function used if none specified
			sets component value to the value from the 
			last piece of given, goal evidence
		"""
		ev, evcount = component.getevidence(model=model, context=context)
		while evcount > 0:
			if ev != None:
				if "goal" in ev.flags:
					component.value = ev.value
					break
				else:
					ev, evcount = component.getevidence(model=model, context=context, count=evcount-1)
					continue
			else:
				component.value = None
				break
		if evcount == 0:
			component.value = None
		component.evidencelist = component.filterevidence(model=self, context=context, resolver_args=resolver_args)
		return component

	def RecentResolver(self, model=None, component=None, context=None, resolver_args=None):
		"""	resolver function used if none specified
			sets component value to the value from the 
			last piece of given, goal evidence
		"""
		ev, evcount = component.getevidence(model=model, context=context)
		
		if resolver_args is None:
			return component
		component.evidencelist = component.filterevidence(model=self, context=context, resolver_args=resolver_args)
		return component

