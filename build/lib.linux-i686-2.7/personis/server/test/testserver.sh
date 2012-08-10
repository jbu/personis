#!/bin/sh
python -m personis.server.server --models=models/ --config=server-test.conf --oauthclients=oauth-clients-test.json --admins=admins-test.yaml --log=INFO
