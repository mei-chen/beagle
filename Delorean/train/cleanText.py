
# encoding=utf8

from __future__ import unicode_literals

from __future__ import print_function, unicode_literals, division
import io
import os
import sys
import time
import re


try:
    import ujson as json
except ImportError:
    import json


def to_unicode(strOrUnicode, encoding='utf-8'):
    '''Returns unicode from either string or unicode object'''
    if isinstance(strOrUnicode, unicode):
        return strOrUnicode
    return unicode(strOrUnicode, encoding, errors='ignore')

def get_file_names(dir_name):
    list_of_files = []
    print(dir_name)
    for root, subdirs, file_names in os.walk(dir_name):
        print(file_names)
        for file_name in file_names:
            if "DS_Store" not in file_name:  # For Mac ONLY
                try:
                    filePath = os.path.join(root, file_name)
                    list_of_files.append(filePath)
                except Exception as e:
                    print(e)
    return list_of_files

def iter_comments(dir_name):
    list_of_files = get_file_names(dir_name)
    for file_name in list_of_files:
        with io.open(os.path.join('./CleanedFiles/', os.path.basename(file_name)+'.clean'), "w",encoding='utf8') as outFile:
            try:
                with io.open(file_name, 'r', encoding='utf16') as f:
                    #str=f.read().replace('\n',' ')
                    str=clean_up(f)
                    outFile.write(str.strip())
            except:
                with io.open(file_name, 'r') as f:
                    #str = f.read().replace('\n', ' ')
                    str = clean_up(f)
                    outFile.write(str.strip())
    return

def clean_up(text):
    str_text = str(text)
    # remove page #
    n = re.compile(r'\n\s*(-)*((Page )[0-9]{1,3}( of ))?[0-9]{1,3}(-)*\s*\n')
    no_page_num_text = re.sub(n, '', str_text)
    # get rid of line breaker
    p=re.compile('\s+')
    clean_text = re.sub(p, ' ', no_page_num_text)
    # remove tag
    notag_text = re.sub(r'</?\w+[^>]*>', '', clean_text)
    return notag_text


if __name__ == '__main__':
    print("start clean files")
    start_time = time.time()
    iter_comments(sys.argv[1])
    print("--- %s seconds ---" % (time.time() - start_time))


