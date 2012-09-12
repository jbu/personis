#!/bin/sh
export PYTHONPATH=../..
python -m personis.server --models=models/ --config=server-test.conf --oauthclients=oauth-clients-test.json --admins=admins-test.yaml --log=DEBUG
