from os import path
import re


def parse_gazette(fname):
    """ Parses plain text one-entity-per-line gazette file """
    entities = set()
    with open(fname) as fin:
        for line in fin:
            clnline = line.strip()
            if clnline and not clnline.startswith('#'):
                entities.add(clnline)
    return entities


LOC_GAZETTE = parse_gazette(path.join(path.dirname(path.abspath(__file__)),
                                      'resources',
                                      'location_gazette.txt'))


LOC_REs = [re.compile(r'\b(%s)\b' % re.escape(loc)) for loc in LOC_GAZETTE]
