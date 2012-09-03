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

#
# Active User Models: added subscribe method to Access

import base
import subscription
from types import *
import re, time
import cronserver


class Access(base.Access):
	'''Access class with active additions

	:param model: Name of the model to open - must resolve, with modeldir, to a valid directory
	:type model: str
	:param modeldir: Directory of the model
	:type modeldir: str
	:param user: Username of person accessing. Should match model owner, but authorization is handled at server level.
	:type user: str

	'''

	def __init__(self, model=None, modeldir=None, user=None):
		base.Access.__init__(self, model=model, modeldir=modeldir, user=user)
	
	def subscribe(self,
		context=[],
		view=None,
		subscription=None):
		"""

		:param context: is a list giving the path of context identifiers
		:param view: is either:
			an identifier of a view in the context specified
			a list of component identifiers or full path lists
			None indicating that the values of all components in the context be returned
		:param subscription: is a dictionary containing owner, password and subscription statement string
		"""
		subscription['modelname'] = self.modelname
		print "subscription>>> %s %s %s" % (repr(context), repr(view), repr(subscription))
		cronsub = subscription["statement"].strip().startswith("[")
		token = "%s:%f" % (self.user, time.time())
		for elt in ("user", "password", "statement"):
			if elt not in subscription:
					raise ValueError, '"%s" key missing from subscription dict' % (elt)
		if len(subscription.items()) != 4:
				raise ValueError, 'unknown attribute in subscription %s'%(subscription)
		#print "token:", token
		self.curcontext = self._getcontextdir(context)
		contextinfo = self.getcontext(context)
		try:
			comps,comps_shelf_fd = base.shelf_open(self.curcontext+"/.components", "r")
		except:
			print "can't open ",self.curcontext+"/.components"
			comps = None
		try:
			views,views_shelf_fd = base.shelf_open(self.curcontext+"/.views", "r")
		except:
			views = None
		try:
			subs,subs_shelf_fd = base.shelf_open(self.curcontext+"/.subscriptions", "w")
		except:
			subs = None
		cidlist = []
		cobjlist = []
		if type(view) is StringType:
			if views != None:
				if not view in views:
					raise ValueError, '"%s" view not found'%(view)
				cidlist = views[view].component_list
			else:
				raise ValueError, '"%s" view not found'%(view)
		elif type(view) is ListType:
			cidlist = view
		elif view == None: 
			if comps != None:
				cidlist = comps.keys()
		else:
			raise TypeError, 'view "%s" has unknown type'%(repr(view))
		for cid in cidlist:
			if type(cid) == type(u""):
				cid = str(cid)
			if type(cid) is StringType:
				if comps != None:
					if cid in comps:
						# add sub dict to subs for cid ######
						if cid in subs:
							newsub = subs[cid]
						else:
							newsub = {}
						newsub[token] = subscription
						subs[cid] = newsub
						if cronsub:
							cronserver.cronq.put(dict(op="put",context=context, comp=cid, subscription=subscription))
					else:
						raise ValueError, 'component "%s" not in view "%s" (%s)'%(cid,view,cidlist)
				else:
					raise ValueError, 'component "%s" not found'%(cid)
			elif type(cid) is ListType:
				vcontext = self._getcontextdir(cid[:-1])
				try:
					vcomps,vcomps_shelf_fd = base.shelf_open(vcontext+"/.components", "r")
				except:
					raise ValueError, 'context "%s" not in view "%s"'%(cid[-1],repr(view))
				if cid[-1] in vcomps:
					# add sub dict to subs for cid[-1] #########
					if cid[-1] not in subs:
						newsub = {}
					else:
						newsub = subs[cid[-1]]
					newsub[token] = subscription
					subs[cid[-1]] = newsub
					if cronsub:
						cronserver.cronq.put(dict(op="put",context=context, comp=cid, subscription=subscription))
				else:
					raise ValueError, 'component "%s" not in view "%s"'%(cid[-1],repr(view))
				base.shelf_close(vcomps, vcomps_shelf_fd)
					
		if comps != None:
			base.shelf_close(comps, comps_shelf_fd)
		if views != None:
			base.shelf_close(views, views_shelf_fd)
		if subs != None:
			base.shelf_close(subs, subs_shelf_fd)
		return token

	def delete_sub(self, context=None, componentid=None, subname=None):
		self.curcontext = self._getcontextdir(context)
		if type(componentid) == type(u''):
			componentid = str(componentid)
		try:
			subs,subs_shelf_fd = base.shelf_open(self.curcontext+"/.subscriptions", "w")
		except:
			raise ValueError, 'no subs db when deleting sub %s for component "%s" in context "%s" not found'%(subname, componentid,self.curcontext)
		if componentid not in subs:
			raise ValueError, 'sub %s for component "%s" in context "%s" not found'%(subname, componentid,self.curcontext)
		subdict = subs[componentid]
		try:
			del subdict[subname]
		except:
			raise ValueError, 'cannot delete subname "%s" for component "%s" in context "%s" '%(subname,componentid,self.curcontext)
		subs[componentid] = subdict
		if subs != None:
			base.shelf_close(subs, subs_shelf_fd)
		return None

	def list_subs(self, context=None, componentid=None):
		self.curcontext = self._getcontextdir(context)
		try:
			subs,subs_shelf_fd = base.shelf_open(self.curcontext+"/.subscriptions", "r")
		except:
			raise ValueError, 'no subs db when listing subs for component "%s" in context "%s" '%(componentid,self.curcontext)
		if componentid not in subs:
			raise ValueError, 'no subs for component "%s" in context "%s" not found'%(componentid,self.curcontext)
		subdict = subs[componentid]
		if subs != None:
			base.shelf_close(subs, subs_shelf_fd)
		return subdict


	def checksubs(self, context, componentid):
		subs,subs_shelf_fd = base.shelf_open(self.curcontext+"/.subscriptions", "r")
		#print ">>>subs in context '%s': %s" % (self.curcontext, subs.keys())
		#print "checking subs for '%s'"%(componentid)
		if componentid in subs:
			subdict = subs[componentid]
			for subname,sub in subdict.items():
				if sub == {}:
					continue
				subscription.dosub(sub, self)

