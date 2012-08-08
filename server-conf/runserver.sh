#!/bin/sh

# If you want to run this on port 80, use authbind. 
# sudo touch /etc/authbind/byport/80
# sudo chown <user>:<user> /etc/authbind/byport/80
# sudo chmod 755 /etc/authbind/byport/80
# And add authbind to the start of the execution below

python -m personis.server.server --models=models/ --config=server.conf --oauthclients=oauth_clients.json --admins=admins.yaml
