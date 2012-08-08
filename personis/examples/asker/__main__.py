#!/usr/bin/env python

from personis import client

import httplib2
from collections import defaultdict


if __name__ == '__main__':

	# get past the uni's stupid proxy server
    p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)

    # Use the util package to get a link to UM. This uses the client_secrets.json file for the um location
    um = client.util.LoginFromClientSecrets(http=httplib2.Http(proxy_info=p))

    # Ask UM for the logged items
    reslist = um.ask(context=["Apps", 'Logging'],view=['logged_items'])

    # Go through the returned evidence and count the number of times each item was logged
    d = defaultdict(int)
    for res in reslist:
    	evlist = res.evidencelist
        for ev in evlist:
        	d[ev.value] += 1

    # get the length of the longest string in the keys of d. Don't try this at home.
    leng = len(reduce(lambda x, y: x if len(x) > len(y) else y, d.keys()))
    # use it to create a format string
    f = '{:>'+`leng + 1`+'} : {}'
    # print the dict using the format
    for k, v in d.items():
    	print f.format(k, '*'*v)