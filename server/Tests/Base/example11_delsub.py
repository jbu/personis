#!/usr/local/bin/python

import Personis
import Personis_a

print "delete a subscription (temp test)"


um = Personis_a.Access(model='Alice', modeldir='Tests/Models', user='alice', password='secret')

reslist = um.ask(context=["Personal"], view='fullname', showcontexts=True)
print reslist
cobjlist, contexts, theviews, thesubs = reslist
subname = thesubs.items()[0][1].items()[0][0]
print "first sub is: ", subname

result = um.delete_sub(context=["Personal"], componentid='lastname', subname=subname)

print result


