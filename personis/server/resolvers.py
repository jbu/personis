#!/bin/env python

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

#
# mixin for Access class containing the resolvers
#

import time,types,traceback,re
import json


class Access:
	"""Resolver mixin for Personis Access

	Contains resolver methods that can be specified on an "ask" operation
	To add a new resolver, add the method to this class and add an
	entry to the self.resolverlist dictionary
	"""
	def __init__(self):
		self.resolverlist = {"default":self._DefaultResolver, "goal":self.GoalResolver, "recent":self.RecentResolver}

	
	def _DefaultResolver(self, model=None, component=None, context=None, resolver_args=None):
		"""resolver function used if none specified
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

