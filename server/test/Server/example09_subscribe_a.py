#!/usr/local/bin/python

import Personis
import Personis_a

print ">>>> subscribe to changes in lastname"

um = Personis.Access(model='Alice', user='alice', password='secret')

sub = """
<default!./Personal/lastname> ~ '.*' :
         NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'lastname=' <./Personal/lastname> 
"""

result = um.subscribe(context=["Personal"], view=['lastname'], subscription={'user':'alice', 'password':'qwert', 'statement':sub})
print result

print ">>>> add a subscription that is checked regularly according to a cron rule"
# min, hour, day of month, month, day of week
sub = """
 ["1-58 * * * *"] <default!./Personal/lastname> ~ '.*' :
         NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'lastname=' <./Personal/lastname> 
"""

result = um.subscribe(context=["Personal"], view=['lastname'], subscription={'user':'alice', 'password':'secret', 'statement':sub})
print result
