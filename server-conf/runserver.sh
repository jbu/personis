#!/bin/sh
python -m personis.server.server --models=models/ --config=server.conf --oauthclients=oauth_clients.json --admins=admins.yaml
