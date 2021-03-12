import os
import re
import sys


OLD = "foodbowl"
PATH = os.path.dirname(os.path.realpath(__file__))

BLACKLIST_FILES = []


def list_dirs(directory):
    for root, subFolders, files in os.walk(directory, topdown=False):
        if '.git' not in root:
            for folder in subFolders:
                yield os.path.join(root, folder)


def list_files(directory):
    for root, subFolders, files in os.walk(directory):
        if '.git' not in root:
            for file in files:
                yield os.path.join(root, file)


def rename(filename, new):
    changed_part = filename[len(PATH):]
    new_name = "%s%s" % (PATH, changed_part.replace(OLD, new))
    os.rename(filename, new_name)
    print("Renamed: '%s' into '%s'" % (filename, new_name))


def replace_keep_case(word, replacement, text):
    def func(match):
        g = match.group()
        if g.islower():
            return replacement.lower()
        if g.istitle():
            return replacement.title()
        if g.isupper():
            return replacement.upper()
        return replacement
    return re.sub(word, func, text, flags=re.I)


def replace_text(filename, new):
    with open(filename) as fin:
        text = fin.read()
    new_text = replace_keep_case(OLD, new, text)
    if new_text != text:
        with open(filename, 'w') as fout:
            fout.write(new_text)
        print "Text replaced in: '%s'" % filename


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: `python initproject.py new_name`")
    NEW = sys.argv[1]

    # Rename directories first
    dirs = list_dirs(PATH)
    for dirname in dirs:
        basename = os.path.basename(dirname)
        if OLD in basename:
            rename(dirname, NEW)

    # Rename files
    files = list_files(PATH)
    for filename in files:
        basename = os.path.basename(filename)
        if OLD in basename:
            rename(filename, NEW)

    # Replace text in files
    files = list_files(PATH)
    for filename in files:
        if filename == os.path.realpath(__file__) or filename in BLACKLIST_FILES:
            continue
        replace_text(filename, NEW)
