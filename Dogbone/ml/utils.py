import re


def party_pattern(party_name):
    return re.compile(r'\b(%s|%s|%s|%s)\b' % (party_name, party_name.lower(), party_name.title(), party_name.upper()))
