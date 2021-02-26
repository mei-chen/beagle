#!/bin/bash

# The Microsoft OneDrive file picker cannot be used over localhost, it requires a valid URL.
# This script uses the localtunnel node app to create a tunnel to localhost:8000 and assign
# it to some URL. The subdomain that is built into this script is currently set to the
# redirect URI for this OneDrive app.

# More info: http://localtunnel.me/

which lt >> /dev/null
if [ $? -eq 0 ]; then
  lt --subdomain corymdbrdk --port 8000
else
  echo "The localtunnel (lt) node app is not installed. If you have node, use"
  echo "  npm install -g localtunnel"
  echo "to run this script for the OneDrive file picker."
fi
