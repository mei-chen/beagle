#!/usr/bin/python

import re
import json

# From environment variables

environment = {}

try:
    conf = open("/etc/supervisor/conf.d/gunicorn.conf").read()
except:
    conf = ""

line = re.search('^environment *= *(.+)$', conf, re.MULTILINE)
if line:
    line = line.group(1) or ""

    for var in line.split(","):
        pair = var.split("=")
        environment[pair[0].strip()] = re.sub('^"|"$', '', pair[1].strip())

if "DATABASE_URL" in environment:
    environment["db_password"] = re.search(':[^:]*:([^@]+)@', environment["DATABASE_URL"]).group(1)

print json.dumps({
    "changed": True,
    "ansible_facts": {
        "gather_secrets": environment
    }
})
