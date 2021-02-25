import re


# Copied and pasted from dogbone.nlplib.utils
number_re = re.compile(r'\b([0-9]+[,.]?)+\b')
fillin_underscore_re = re.compile(r'\b(_+)\b')
