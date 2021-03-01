# -*- coding: utf-8 -*-
#necessary includes
from __future__ import division
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import io
import os
# necessary includes
import cchardet

import re
import time
from collections import Counter
from string import lower

import nltk.data
from nltk.tokenize import word_tokenize
# from nltk.parse import stanford
from nltk.tree import ParentedTree
from nltk.tree import Tree

import StanfordParser

WORD_COUNT_LIMIT = 150
TOLERANCE = 0.130
UPPER_CASE_TOL = 0.66



class definitions():

    def __init__(self):
        self.stopWordFile = load_stopwords('././DefinitionTools/stopwords.txt')

    def __call__(self, file):
        fileStream=read_file(file.file.read())

        return self.extract(self.stopWordFile,fileStream)


    def extract(self,stopwords,text):

        # compile the regular expression pattern
        # consective words with the first letter uppercased
        pattern = re.compile("([a-z0-9]*[A-Z][/\w-]*([ \t\r\f\v]*[0-9]*[A-Z0-9][/\w-]*)*)")


        ##### count the occurrence of each token


        WordOccurrenceHash = construct_word_hash(text)
        print WordOccurrenceHash
        ##### coun the terms matching the pattern and their locations in the text
        TermOccurrenceHash = construct_term_hash(pattern, text, stopwords)

        # get the text divided into sentences (tokenize it) and the starting localtion
        listTextSentences = tokenize_text(text)

        len_init = len(TermOccurrenceHash)

        ##### remove single words which might be the first word in sentence
        self.eliminate_improbable_terms(TermOccurrenceHash, WordOccurrenceHash, listTextSentences)

        # print 'Number of initial terms:', len_init
        # print 'Number of terms after elimination:', len(TermOccurrenceHash), '\n'

        del WordOccurrenceHash

        print 'Definitions from Stanford Parser'

        start = time.time()
        termDefinitionHash={}



        try:
            termDefinitionHash = self.construct_dictionary(pattern, listTextSentences, TermOccurrenceHash)
        except Exception, e:
            print e

        definitions={}
        definitions['definitions']=[]
        if termDefinitionHash!={}:
            keys = termDefinitionHash.keys()

            for key in keys:
                if termDefinitionHash[key] != "":
                    tempDef={}
                    tempDef["Definition"] = termDefinitionHash[key].replace('-LRB- ', '(').replace(' -RRB-', ')')
                    tempDef["Term"] = key
                    definitions['definitions'].append(tempDef)

            definitions['Time']=str(time.time() - start)
            return definitions
        else:
            return {}
        #print str(time.time() - start)

    ### the prob of the key actually lowercased in the text
    def probability_1 (self,key, WordOccurrenceHash):
        if key.lower() in WordOccurrenceHash.keys():
            return WordOccurrenceHash[key] / (WordOccurrenceHash[key] + WordOccurrenceHash[key.lower()])
        else:
            return 1.0


    ##### The key is NOT the first word in sentences
    def probability_2 (self,key, listTextSentences, TermOccurrenceHash):
        count = 0

        for pos in TermOccurrenceHash[key] :
            if pos in [x[1] for x in listTextSentences] :
                count += 1

        return 1 - count / len(TermOccurrenceHash[key])


    def probability_3 (self,key, TermOccurrenceHash, capitalMaxOccurrence, capitalMinOccurrence, averageOccurrence):
        capitalApparitionRelevance = len(TermOccurrenceHash[key]) / capitalMaxOccurrence
        rangeRelevance = (capitalMaxOccurrence - capitalMinOccurrence) / capitalMaxOccurrence
        if capitalMaxOccurrence - capitalMinOccurrence == 0 :
            dispositionRelevance = 1
        else :
            dispositionRelevance = 1 - abs((capitalMaxOccurrence + capitalMinOccurrence) / 2 - averageOccurrence) / (capitalMaxOccurrence - capitalMinOccurrence)

        return capitalApparitionRelevance * rangeRelevance * dispositionRelevance

    def eliminate_improbable_terms(self,TermOccurrenceHash, WordOccurrenceHash, listTextSentences):
        omega_1 = 0.165
        omega_2 = 0.035
        omega_3 = 0.800

        #max number of occurrence

        if TermOccurrenceHash!={}:
            capitalMaxOccurrence = max([len(TermOccurrenceHash[x]) for x in TermOccurrenceHash])
        #min number of occurrence
            capitalMinOccurrence = min([len(TermOccurrenceHash[x]) for x in TermOccurrenceHash])
        # average number of occurrence
            averageOccurrence = sum([len(TermOccurrenceHash[x]) for x in TermOccurrenceHash]) / len(TermOccurrenceHash)
        else:
            capitalMaxOccurrence =0
            capitalMinOccurrence=0
            averageOccurrence=0
        keys = TermOccurrenceHash.keys()


        #### clean up terms of single word
        for key in keys :
            if ' ' not in key :
                p_1 = self.probability_1(key, WordOccurrenceHash)
                p_2 = self.probability_2(key, listTextSentences, TermOccurrenceHash)
                p_3 = self.probability_3(key, TermOccurrenceHash, capitalMaxOccurrence, capitalMinOccurrence, averageOccurrence)

                P = omega_1 * p_1 - omega_2 * p_2 + omega_3 * p_3

                if P < TOLERANCE :
                    del TermOccurrenceHash[key]


    def containing_sentence(self,listTextSentences, starting_index):
        leftLimit = 0
        rightLimit = len(listTextSentences) - 1

        while rightLimit - 1 != leftLimit:
            middle = (rightLimit + leftLimit) // 2
            #print starting_index, leftLimit, rightLimit, middle
            if starting_index == listTextSentences[middle][1]:
                return middle
            elif starting_index < listTextSentences[middle][1]:
                rightLimit = middle
            else:
                leftLimit = middle

        return leftLimit

    # solves the case: <Term> means <Definition>
    def solve_met1(self,term, sent, index, Quoted):
        # find the term position in sent and ignore everything left of it
        index_it = 0
        start = 0

        while index_it < index :
            try:
                index_word = sent.find(term, start)
            except:
                print sent
            index_it += 1
            start = index_word + 1

        offset = 1 if Quoted else 0

        #ptree = ParentedTree.convert(parser.raw_parse(sent[index_word - offset: ]).next())

        ptree = ParentedTree.convert(make_tree(StanfordParser.StanfordRSParser(sent[index_word - offset:])))

        # find the term index, within the leaves
        term_index = find(ptree.leaves(), nltk.word_tokenize(term))[0]

        if term_index == -1:
            return ""
        # using the term index, obtain the road to the term subtree
        term_road = list(ptree.leaf_treeposition(term_index))[ : -1]
        # using the road, obtain the actual term subtree
        term_tree = ptree[term_road]


        # find the nearest S, looking up from the term_tree
        S_tree = term_tree

        while S_tree.label() != u'S' :
            S_tree = S_tree.parent()

            if S_tree == None :
                return ""

        # find the first VP child of S
        # it will contain a VBZ separating the term from the definition (contained it the same VP)
        VP_tree = None

        for subtree in S_tree :
            if subtree.label() == u'VP' :
                VP_tree = subtree
                break

        if VP_tree == None :
            return ""

        # search in the VP subtree of S for the first VBZ
        VBZ_tree = getLabeledNode(VP_tree, u'VBZ')

        if VBZ_tree == None :
            return ""

        # search right of the VBZ to find the first NP
        # it will contain the definition
        it = VBZ_tree.right_sibling()
        NP_tree = None

        while it != None :
            if it.label() == u'NP' :
                NP_tree = it
                break

            NP_tree = getLabeledNode(it, u'NP')
            if NP_tree != None :
                break

            it = it.right_sibling()

        if NP_tree == None :
            return ""

        return ' '.join(NP_tree.leaves())

    # search the children of an element in order do find a <bracket> label
    # also search for extra children who can affect the definition extraction algorithm
    # NOTE: children must not be words; only tags(reason for del road[-2:] before calling this function)
    def getInitialInfo(self,ptree):
        extra_words = 0                       # take note of the words that are not part of the term structure, but of the definition
        bracket_found = False           # make sure we actually find a bracket, first of all
        unwanted_child_found = False    # if we have "unwanted children" after the term structure, we need to consider a new definition structure case

        for subtree in ptree :
            if subtree.label() == u'-LRB-' :    # we have successfully found the starting marker of the term structure
                bracket_found =  True
            if bracket_found == False :         # until we find the ending marker, all structures will be part of the definition
                extra_words += 1

        if subtree.label() != u'-RRB-' :        # if the last label found was not the end of the term structure
            unwanted_child_found = True

        return (extra_words, bracket_found, unwanted_child_found)

    # solves the case: [...] <Definition> ([...] <Term>) [...]
    def solve_met2 (self,term, sent, pos) :
        return_string = ""
        #ptree = ParentedTree.convert(parser.raw_parse(sent).next())
        #ptree = ParentedTree.convert(StanfordParser.StanfordRSParser(sent))

        ptree=ParentedTree.convert(make_tree(StanfordParser.StanfordRSParser(sent)))

        matches = find(ptree.leaves(), nltk.word_tokenize(term))

        if len(matches) < pos :
            return ""

        term_index = matches[pos-1]
        if term_index == -1:
            return ""

        # using the term index, obtain the road to the term subtree
        term_road = list(ptree.leaf_treeposition(term_index))[ : -2]


        # using the road, obtain the actual term subtree
        term_tree = ptree[term_road]

        # if the brackets are not included in a PRN, but in something like a NP
        # get the number of leaves that are found before the first bracket
        lbr_start_pos, bracket_found, unwanted_child_found = self.getInitialInfo(term_tree)

        tree_it = term_tree

        while not bracket_found and tree_it != ptree:

            tree_it = tree_it.parent()

            lbr_start_pos, bracket_found, unwanted_child_found = self.getInitialInfo(tree_it)

        # term_strucutre_tree is the subtree that contains the Term but whose leafs will not appear in the definition
        term_structure_tree = tree_it

        if tree_it != ptree:
            # obtain the road to the farthest NounPhrase (start of the definition)
            #tree_it = tree_it.parent()
            NP_tree = None
            # find the road to the NP closest to S
            while tree_it.label() != u'S' and tree_it.label() != u'ROOT':
                if tree_it.label() == u'NP' :
                    NP_tree = tree_it

                tree_it = tree_it.parent()

            S_tree = tree_it
            if S_tree.label() == u'ROOT' :
                return ""

            # if we have a particular form of this definition type
            # go all the way up to the nearest S in stead of NP (iterator is already there)
            if unwanted_child_found == True or NP_tree == None :
                NP_tree = S_tree

            # create the string that is to be returned
            # initialize the string with the elements of the farthest NP but stop before entering the Term Structure
            return_string = NP_tree.leaves()[0 : find(NP_tree.leaves(), term_structure_tree.leaves())[0]]

            #if the Term Structure was not a PRN, add to the string the words contained in the Term Structure that are located before the -LRB-
            it = 0
            while it < lbr_start_pos :
                return_string += term_structure_tree[it].leaves()
                it += 1

            # raise SBAR special case warning flag
            if tree_it.parent().label() == u'SBAR' :
                # we have SBAR special case
                if NP_tree.parent() != S_tree :
                    # take the entire content of the definition NP
                    aux_string = NP_tree.leaves()
                    # take the content of the term structure (inside the definition NP)
                    aux_substring = term_structure_tree.leaves()
                    # find the latter inside the former
                    discontinue_pos = find(aux_string, aux_substring)[0]
                    # return the difference of the two
                    return_string = return_string + aux_string[discontinue_pos + len(aux_substring) : ]

        # return the definition (text between the first leaf of defStartWord parent and the Term Structure)
        return  ' '.join(return_string)


    #def extract_definition(term, sentence, parser, term_occurence_in_sent):
    def extract_definition(self,term, sentence, term_occurence_in_sent):

        print term
        print sentence
        print term_occurence_in_sent

        # if the sentence is too long, it is not definition
        if sentence.count(' ') + 1 > WORD_COUNT_LIMIT:
            return ""
        #save the term as a string for later processing
        term_string = term
        #turn the string into unicode
        #term = term.decode("UTF-8")
        #tokenize the term. Helpful when term contains multiple words
        term = nltk.word_tokenize(term)

        #get length of the term
        term_length = len(term)

        #use the nltk parser on the sentence
        #sentences = parser.raw_parse(sentence.replace('(',' ('))
        #print sentence

        sentences = StanfordParser.StanfordRSParser(sentence.replace("'", "\'").replace('(', ' (').replace('"', '\"'))


        #in case the parse tree has multiple roots(can happen with in-line newlines)

        #root = sentences.next()
        root = make_tree(sentences)

        termIndex = find_correct_index(term, sentence, term_occurence_in_sent)

        if len(root.leaves()) >= term_length:
            if has_brackets(sentence, term_string, term_occurence_in_sent):
                return self.solve_met2(term_string, sentence, termIndex)

            elif has_quotes(root.leaves(), term, termIndex):
                return self.solve_met1(term_string, sentence, termIndex, True)
            else:
                if any(x in sentence for x in ('means','shall mean','refers','shall refer')):
                    sentence=sentence.replace(term_string,'\"'+term_string+'\"')
                    termIndex = find_correct_index(term, sentence, term_occurence_in_sent+1)
                    return self.solve_met1(term_string, sentence, termIndex, True)

        return ""

    def construct_dictionary(self,pattern, listTextSentences, TermOccurrenceHash):
        #construct the parser
        #parser = initialize_parser(pathToMain)
        #initialize term->definition dictionary
        termDefinitionHash = {}
        #print TermOccurrenceHash

        it = 1
        total = len(TermOccurrenceHash.keys())

        for term in TermOccurrenceHash.keys():
            #print '[', it, '/', total, ']'
            it += 1
            #print term
            lastProcessedSentence = -1
            termIndex = 0

            for starting_index in TermOccurrenceHash[term]:
                #print containing_sentence(listTextSentences, starting_index), term

                currentContainingSentence = self.containing_sentence(listTextSentences, starting_index)

                #whether the sentence has uppercase >2/3
                if isUpperCase(listTextSentences[currentContainingSentence][0]):
                    continue

                if lastProcessedSentence != currentContainingSentence:
                    termIndex = 1
                else:
                    termIndex += 1

                #print term, ">>>", listTextSentences[currentContainingSentence][0].encode('utf-8')

                #definition = extract_definition(term, listTextSentences[currentContainingSentence][0], parser, starting_index - listTextSentences[currentContainingSentence][1])

                definition = self.extract_definition(term, listTextSentences[currentContainingSentence][0],starting_index - listTextSentences[currentContainingSentence][1])

                lastProcessedSentence = currentContainingSentence

                if definition != "":
                    termDefinitionHash[term] = definition

                    break

        return termDefinitionHash


#########################################################

#function that loads stop words from file
def load_stopwords(stopwordsFile):
    f = open(stopwordsFile)
    text = f.read()
    return text.split()

def is_stopword(term, stopwords):
    term_lower = term.lower()
    return term_lower in stopwords

def to_unicode(strOrUnicode, encoding='utf-8'):
    '''Returns unicode from either string or unicode object'''
    if isinstance(strOrUnicode, unicode):
        return strOrUnicode
    return unicode(strOrUnicode, encoding, errors='ignore')

def read_file(fileStream):
    tempLines = fileStream.split("\n")
    text=''
    for line in tempLines:
        if not line.strip():
            continue
        else:
            text=text+' '+line.rstrip()
    text=convert_encoding(text)

    return text

    # try:
    #     text=text.decode('ascii','ignore')
    #     print 'this is ASCII'
    #     return convert_encoding(text)
    # except:
    #
    # # text = text.replace(u"\u201C", '"')  # left double
    # # text = text.replace(u'or "', 'or " ')   # to handle "Term1" or "Term2"
    # # text = text.replace(u"\u201D", '" ') # right double
    # # text = text.replace(u"\u2018", "' ") # left single
    # # text = text.replace(u"\u2019", "' ") # right single
    #
    #     return text.decode('utf-8','ignore')
def make_tree(result):
    return Tree.fromstring(result)

def parse_trees_output(output_):
        res = []
        cur_lines = []
        cur_trees = []
        blank = False
        for line in output_.splitlines(False):
            if line == '':
                if blank:
                    res.append(iter(cur_trees))
                    cur_trees = []
                    blank = False
                # elif _DOUBLE_SPACED_OUTPUT:
                #     cur_trees.append(_make_tree('\n'.join(cur_lines)))
                #     cur_lines = []
                #     blank = True
                else:
                    res.append(iter([make_tree('\n'.join(cur_lines))]))
                    cur_lines = []
            else:
                cur_lines.append(line)
                blank = False
        return iter(res)

def tokenize_text(text):
    #load the tokenizer
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    #divide the text into sentences using the tokenizer
    tokenizedText = tokenizer.tokenize(text)

    #initialize the resulting list
    listTextSentences = []

    #split the text where \n is found
    #iterate over tokenized sentences
    for sentence in tokenizedText:
        #iterate over the divisions caused by '\n' in the current sentence
        for division in sentence.split('\n'):
            #for successive newlines, this condition is necessary
            if len(division) > 0:
                #append current division to the resulting list
                sentence_pattern = re.compile(re.escape(division))
                iterations = sentence_pattern.finditer(text)

                temporary_list = list(iterations)
                if temporary_list != []:
                    sentenceStartingIndex = temporary_list[0].start()

                    listTextSentences.append((division, sentenceStartingIndex))

    i = 0
    while i < len(listTextSentences) - 1 :
        if len(listTextSentences[i+1][0]) < 5 :
            listTextSentences[i] = (listTextSentences[i][0] + ' ' + listTextSentences[i+1][0], listTextSentences[i][1])
            del listTextSentences[i+1]
        else :
            m = re.search("[a-zA-Z()]", listTextSentences[i+1][0])
            if m and listTextSentences[i+1][0][m.start()].islower() :
                listTextSentences[i] = (listTextSentences[i][0] + text[listTextSentences[i][1] + len(listTextSentences[i][0]) : listTextSentences[i+1][1]] + listTextSentences[i+1][0], listTextSentences[i][1])
                del listTextSentences[i+1]
            else :
                i += 1

    listTextSentences.append(("", len(text)))

    return listTextSentences

def substr_in_list(substr, keys):
    substr = lower(substr)
    return_list = []

    for key in keys :
        if substr in lower(key) :
            return_list.append(key)

    return return_list

def construct_term_hash(pattern, text, stopwords):
    TermOccurrenceHash = {}

    it = 0
    word_list = []

    # identify all potential terms
    for match in pattern.finditer(text):
        if match.group() not in word_list :
            word_list.append(match.group())
            it += 1
      #### add locations of the term
        if not (' ' not in match.group() and is_stopword(match.group(), stopwords)):
            if match.group() in TermOccurrenceHash.keys():
                TermOccurrenceHash[match.group()].append(match.start())
            else:
                TermOccurrenceHash[match.group()] = [match.start()]


    # remove singular occurrence terms
    for key in TermOccurrenceHash.keys() :
        space_count = key.count(' ')
        drv_lst = substr_in_list(key, TermOccurrenceHash.keys())
        occ = 0

        for newKey in drv_lst :
            if space_count != 0 or (space_count == 0 and newKey.count(' ') == space_count):
                occ += len(TermOccurrenceHash[newKey])

    # print 'terms + stopwords: ', it, '\n'

    return TermOccurrenceHash

def construct_word_hash(text):
    WordOccurenceHash = {}

    tokenizedText = word_tokenize(text)

    return Counter(tokenizedText)

def isUpperCase(text):
    p_l = re.compile("[a-z]")
    p_u = re.compile("[A-Z]")

    lower_count = len(p_l.findall(text))
    upper_count = len(p_u.findall(text))

    r = upper_count / (lower_count + upper_count)

    return r > UPPER_CASE_TOL

# checks if a term is inside quotation marks
def has_quotes(sentence, term, count):
    matches = find(sentence, term)
    if len(matches) < count :
        return False

    position = matches[count - 1]

    term_length = len(term)

    quotes_left = nltk.word_tokenize('"x"')[0]
    quotes_right = nltk.word_tokenize('"x"')[2]

    #if the term can have quotation marks and if it does
    if position > -1 and len(sentence) - term_length != position:

        if sentence[position - 1] == quotes_left and sentence[position + term_length] == quotes_right:
            return True

    return False

# checks if a word is inside a bracket structure
def has_brackets(text, word, pos) :
    # find the word that we are looking for
    try:
        index_word = pos
    except:
        print pos

    # we ran out of words before reaching the one that we needed
    if index_word == -1 :
        return False

    # check if the word is outside of a bracket structure
    index_lrb = text[ : index_word].rfind('(')
    index_rrb = text[ : index_word].rfind(')')

    if index_rrb >= index_lrb :
        return False

    index_lrb = text[index_word : ].find('(')
    index_rrb = text[index_word : ].find(')')

    if index_rrb == -1 or (index_lrb != -1 and index_lrb < index_rrb) :
        return False

    return True

# returns the starting positions of a sublist in a list
def find(lst, sublst):
    n = len(sublst)
    positions = []

    for i in xrange(len(lst) - n + 1) :
        if sublst == lst[i:i+n] :
            positions.append(i)

    if positions == [] :
        positions.append(-1)

    return positions

# finds the closest subtree that has as root a node with a certain label
def getLabeledNode2 (tree, label):
    node = None
    for subtree in tree :
        if subtree.height() > 1 and subtree.label() == label :
            return subtree
        if subtree.leaves()[0] != subtree[0] :
                node = getLabeledNode(subtree, label)
                if node != None :
                    return node

    return None

def getLabeledNode (tree, label):
    if tree.label() == label:
        return tree

    if tree.height() > 2 :
        for subtree in tree :
            if subtree.height() > 1:
                node = getLabeledNode(subtree, label)
                if node != None :
                    return node

    return None

def find_correct_index(substr, our_str, pos):
    count = 0

    substr = ' '.join(substr)

    for it in re.finditer(substr, our_str) :
        if it.start() <= pos :
            count += 1;

    return count


def convert_encoding(data, new_coding = 'UTF-8'):
    encoding = cchardet.detect(data)['encoding']
    print encoding

    if new_coding.upper() != encoding.upper():
      data = data.decode(encoding, data.replace('\0','')).encode(new_coding)

    return data