import sys
import  os
import io
import re
import time
import spacy
import csv
from operator import itemgetter
from nltk.tokenize import word_tokenize,sent_tokenize

import spacy



class partyIdentifier(object):


    def __init__(self, spacy_nlp):
        self.nlp = spacy_nlp

    def __call__(self, file):
        lines=extractLines(file.file.read())


        return self.partyIdentifier(self.nlp,lines)

    ##One line contains "(discloser)", and another line has "(disclosee)"
    def partyIdentifyCase1(self,nlp,lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties={}
        parties['party1']={}
        parties['party2'] = {}
        parties['party1']["FullName"]=""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1=None
        line2=None

        # pick the two lines containing disclosureParty and receivingParty, respectively.
        for lineNubmer in range(len(lines)):
            if any(i in lines[lineNubmer] for i in disclosureParty):
                line1=lineNubmer
            if any(i in lines[lineNubmer] for i in receivingParty):
                line2=lineNubmer
            if line1!=None and line2!=None:
                break

        # the two lines must different
        if line1!=None and line2!=None and line1!=line2:
            keyPattern = re.compile("\((.*?)\)")
            key1=""
            for each in keyPattern.finditer(lines[line1]):

                # don't count ABN(bank number) and ACN(company number)
                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key1 = each.group().replace(")", "").replace("(", "")

            # if "Discloser" in key:
            # Use spacy to find the first party name
            if key1:
                if any(i in key1 for i in disclosureParty):
                    doc = nlp(unicode(lines[line1], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']["Role"] = 'Discloser'

            key2 = ""
            for each in keyPattern.finditer(lines[line2]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key2 = each.group().replace(")", "").replace("(", "")


            if key2:
                if any(i in key2 for i in receivingParty):
                    doc = nlp(unicode(lines[line2], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party2']["FullName"] = ent.text
                            parties['party2']["Role"] = 'Disclosee'

            return parties

        else:
            return parties

    ##Only one line contains "(disclosee)", no line has "(discloser)"
    def partyIdentifyCase2(self,nlp,lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties={}
        parties['party1']={}
        parties['party2'] = {}
        parties['party1']["FullName"]=""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1 = None
        line2 = None

        for lineNubmer in range(len(lines)):
            if any(i in lines[lineNubmer] for i in receivingParty):
                line2 = lineNubmer
            if line2 != None:
                break


        key2 = ""
        keyPattern = re.compile("\((.*?)\)")


        if line2!=None:

            for each in keyPattern.finditer(lines[line2]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key2 = each.group().replace(")", "").replace("(", "")

            if key2:
                if any(i in key2 for i in receivingParty):
                    doc = nlp(unicode(lines[line2], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party2']["FullName"] = ent.text
                            parties['party2']["Role"] = 'Disclosee'


            key1=""
            #check each from line2 up to the frist line, whether there is "(" and
            for i in reversed(range(line2)):
                    if "(" in lines[i]:
                        doc = nlp(unicode(lines[i], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_=="ORG":
                                line1=i
                        break
            # check each from line2 down to the last line
            if line1==None:
                for i in (range(line2+1,len(lines))):
                    if "(" in lines[i]:
                        doc = nlp(unicode(lines[i], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_=="ORG":
                                line1=i
                        break
            if line1!=None:
                for each in keyPattern.finditer(lines[line1]):

                    if "ABN" in each.group() or "ACN" in each.group():
                        continue
                    else:
                        key1 = each.group().replace(")", "").replace("(", "")

                if key1:
                    if any(i in key1 for i in disclosureParty):
                        doc = nlp(unicode(lines[line1], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_ == 'ORG':
                                parties['party1']["FullName"] = ent.text
                                parties['party1']["Role"] = 'Discloser'

                    else:
                        doc = nlp(unicode(lines[line1], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_ == 'ORG':
                                parties['party1']["FullName"] = ent.text
                                parties['party1']["ShortName"] = key1
                                parties['party1']["Role"] = 'Discloser'

                return parties
            else:
                return parties
        else:
            return parties

    ##Only one line contains "(discloser)", no line has "(disclosee)"
    def partyIdentifyCase3(self, nlp, lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties = {}
        parties['party1'] = {}
        parties['party2'] = {}
        parties['party1']["FullName"] = ""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1 = None
        line2 = None

        for lineNubmer in range(len(lines)):
            if any(i in lines[lineNubmer] for i in disclosureParty):
                line1 = lineNubmer
            if line1 != None:
                break


        keyPattern = re.compile("\((.*?)\)")

        key1 = ""
        if line1!=None:
            for each in keyPattern.finditer(lines[line1]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key1 = each.group().replace(")", "").replace("(", "")

            if key1:

                if any(i in key1 for i in disclosureParty):
                    doc = nlp(unicode(lines[line1], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']["Role"] = 'Discloser'



        # check lines from line1 down to the last line
            for i in range(line1+1,len(lines)):
                if "(" in lines[i]:
                        doc = nlp(unicode(lines[i], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_=="ORG":
                                line2 = i
                        break

            key2 = ""
            if line2!=None:
                for each in keyPattern.finditer(lines[line2]):
                    if "ABN" in each.group() or "ACN" in each.group():
                        continue
                    else:
                        key2 = each.group().replace(")", "").replace("(", "")

                if key2:
                    if any(i in key2 for i in receivingParty):
                        doc = nlp(unicode(lines[line2], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_ == 'ORG':
                                parties['party2']["FullName"] = ent.text
                                parties['party2']["Role"] = 'Disclosee'
                    else:
                        doc = nlp(unicode(lines[line2], 'utf-8'))
                        for ent in doc.ents:
                            if ent.label_ == 'ORG':
                                parties['party2']["FullName"] = ent.text
                                parties['party2']["ShortName"] = key2
                                parties['party2']["Role"] = 'Disclosee'
                return parties
            else:
                return parties
        else:
            return parties

    ## First party and Second party
    def partyIdentifyCase4(self,nlp,lines): ##contains only "(disclosuree)"

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties={}
        parties['party1']={}
        parties['party2'] = {}
        parties['party1']["FullName"]=""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1=None
        line2=None

        for i in range(len(lines)):
                if 'first party' in lines[i].lower():
                    if lines[i].lower()=='first party' or lines[i].lower()=='first party:':
                        line1=i+1
                    else:
                        line1 = i
                if line1!=None:
                    break
        for i in range(len(lines)):
                if 'second party' in lines[i].lower():
                    if lines[i].lower()=='second party' or lines[i].lower()=='second party:':
                        line2=i+1
                    else:
                        line2 = i
                if line2!=None:
                    break



        if line1==None or line2==None:
            return parties
        else:
            keyPattern = re.compile("\((.*?)\)")
            key1 = ""
            lines[line1]=lines[line1].replace("first party ","").replace("First Party: ","")
            for each in keyPattern.finditer(lines[line1]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key1 = each.group().replace(")", "").replace("(", "")


            if key1:
                if any(i in key1 for i in disclosureParty):
                    doc = nlp(unicode(lines[line1], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']["Role"] = 'Discloser'
                else:
                    doc = nlp(unicode(lines[line1], 'utf-8'))

                    for ent in doc.ents:
                        print (ent.text,ent.label_)
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']['ShortName']=key1
                            parties['party1']["Role"] = 'Discloser/Disclosee'

            else:
                doc = nlp(unicode(lines[line1], 'utf-8'))
                for ent in doc.ents:
                    if ent.label_ == 'ORG':
                        parties['party1']["FullName"] = ent.text
                        parties['party1']["Role"] = 'Discloser/Disclosee'



            key2 = ""

            for each in keyPattern.finditer(lines[line2]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key2 = each.group().replace(")", "").replace("(", "")

            if key2:
                if any(i in key2 for i in receivingParty):
                    doc = nlp(unicode(lines[line2], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party2']["FullName"] = ent.text
                            parties['party2']["Role"] = 'Disclosee'
                else:
                    doc = nlp(unicode(lines[line2], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party2']["FullName"] = ent.text
                            parties['party2']['ShortName'] = key2
                            parties['party2']["Role"] = 'Discloser/Disclosee'

            else:
                doc = nlp(unicode(lines[line2], 'utf-8'))
                for ent in doc.ents:
                    if ent.label_ == 'ORG':
                        parties['party2']["FullName"] = ent.text
                        parties['party2']["Role"] = 'Discloser/Disclosee'

            return parties

    ## I, person
    def partyIdentifyCase5(self,nlp,lines): ##contains only "(disclosuree)"

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties={}
        parties['party1']={}
        parties['party2'] = {}
        parties['party1']["FullName"]=""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1 = None
        line2 = None

        for i in range(len(lines)):
            if 'to:' in lines[i].lower():
                if lines[i].lower()=='to:':
                    line1 = i+1
                else:
                    line1=i
            if line1 != None:
                break

        if line1!=None:
            for i in range(line1,len(lines)):
                if 'i,' in lines[i].lower():
                    line2=i
                if line2 != None:
                    break

        if line1 == None or line2 == None:
            return parties
        else:
            keyPattern = re.compile("\((.*?)\)")
            key1 = ""
            lines[line1] = lines[line1].replace("to ", "").replace("to: ", "")
            for each in keyPattern.finditer(lines[line1]):

                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key1 = each.group().replace(")", "").replace("(", "")

            if key1:
                if any(i in key1 for i in disclosureParty):
                    doc = nlp(unicode(lines[line1], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']["Role"] = 'Discloser'
                else:
                    doc = nlp(unicode(lines[line1], 'utf-8'))
                    for ent in doc.ents:
                        if ent.label_ == 'ORG':
                            parties['party1']["FullName"] = ent.text
                            parties['party1']['ShortName'] = key1
                            parties['party1']["Role"] = 'Discloser'

            else:
                doc = nlp(unicode(lines[line1], 'utf-8'))
                for ent in doc.ents:
                    if ent.label_ == 'ORG':
                        parties['party1']["FullName"] = ent.text
                        parties['party1']["Role"] = 'Discloser'


            parties['party2']["Role"] = 'Disclosuree'
            parties['party2']["ShortName"] = ""

            if line2!=None:
                doc = nlp(unicode(lines[line2],'utf-8'))
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        parties['party2']["FullName"] = ent.text

                return parties
            else:
                return parties


    ## between, and in one sentence
    def partyIdentifyCase6(self,nlp,lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]
        parties={}
        parties['party1']={}
        parties['party2'] = {}
        parties['party1']["FullName"]=""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1=None

        for i in range(len(lines)):
                line = lines[i]
                if "is made" in line.lower() or "entered" in line.lower() or ("between" in line.lower() and "and" in line.lower()):
                    line1=i
                if line1!=None:
                    break

        print lines[line1]

        if line1==None:
            return  parties

        else:
            newLine=""
            try:
                temp=sent_tokenize(lines[line1])
            except:
                temp = sent_tokenize(lines[line1].decode('utf-8'))

            for each in temp:

                if "made" in line.lower():
                        newLine=each
                        newLine = RemoveFromStartTo(newLine, "made")
                        break
                elif "entered" in line.lower():
                        newLine=each
                        newLine = RemoveFromStartTo(newLine, "entered")
                        break
                elif "between" in line.lower():
                        newLine = each
                        newLine = RemoveFromStartTo(newLine, "between")
                        break

            pattern = re.compile("([a-z0-9]*[A-Z][/\w-]*([ \t\r\f\v]*[0-9]*[A-Z0-9][/\w-]*)*)")

            keys=[]
            if newLine!='':
                keyPattern = re.compile("\((.*?)\)")
                for each in keyPattern.finditer(newLine):
                    key = {}
                    if "ABN" in each.group() or "ACN" in each.group():
                        continue
                    else:
                        key['key']=each.group().replace(")","").replace("(","")
                        key['start']=each.start()
                        key['end'] = each.end()
                        keys.append(key)

                party1_start=0
                party1_end = 0
                party2_start = 0
                party2_end = 0


                for each in pattern.finditer(newLine):
                    print each.group()
                    doc=nlp("This is "+unicode(each.group().replace(")","").replace("(","")))
                    for ent in doc.ents:
                        if ent.label_=='ORG':
                            parties['party1']["FullName"] =ent.text
                            party1_start=each.start()
                            party1_end =each.end()
                            break
                    break
                #print newLine

                newLine1=RemoveFromStartAfter(newLine,parties['party1']["FullName"])


                doc=nlp(unicode(newLine1))

                for ent in doc.ents:
                    if ent.label_=="ORG":
                        parties['party2']["FullName"] = ent.text
                        break

                print parties

                for each in pattern.finditer(newLine):
                    if parties['party2']["FullName"].replace(".","") in each.group():
                        party2_start=each.start()
                        party2_end = each.end()


                if len(keys)==0:
                    parties['party1']["ShortName"] = ""
                    parties['party1']["Role"] = 'Discloser/Disclosee'
                    parties['party2']["ShortName"] = ""
                    parties['party2']["Role"] = 'Discloser/Disclosee'
                    return parties
                if len(keys)==1:

                    #check the index of keys, before and after the parties.

                    if keys[0]['end']<party2_start:
                        if any(i in keys[0]['key'] for i in disclosureParty):
                            parties['party1']["ShortName"] = ""
                            parties['party1']["Role"] = 'Discloser'
                            parties['party2']["ShortName"] = ""
                            parties['party2']["Role"] = 'Disclosee'
                        else:
                            parties['party1']["ShortName"] = keys[0]['key']
                            parties['party1']["Role"] = 'Discloser/Disclosee'
                            parties['party2']["ShortName"] = ""
                            parties['party2']["Role"] = 'Discloser/Disclosee'
                    if keys[0]['start']>party2_end:
                        if any(i in keys[0]['key'] for i in receivingParty):
                            parties['party2']["ShortName"] = ""
                            parties['party2']["Role"] = 'Disclosee'
                            parties['party1']["ShortName"] = ""
                            parties['party1']["Role"] = 'Discloser'
                        else:
                            parties['party2']["ShortName"] = keys[0]['key']
                            parties['party2']["Role"] = 'Discloser/Disclosee'
                            parties['party1']["ShortName"] = ""
                            parties['party1']["Role"] = 'Discloser/Disclosee'
                    return parties
                if len(keys) == 2:

                    if any(i in keys[0]['key'] for i in disclosureParty):
                        parties['party1']["ShortName"] = ""
                        parties['party1']["Role"] = 'Discloser'
                    else:
                        parties['party1']["ShortName"] = keys[0]['key']
                        parties['party1']["Role"] = 'Discloser/Disclosee'

                    if any(i in keys[1]['key'] for i in receivingParty):
                        parties['party2']["ShortName"] = ""
                        parties['party2']["Role"] = 'Disclosee'
                    else:
                        parties['party2']["ShortName"] = keys[1]['key']
                        parties['party2']["Role"] = 'Discloser/Disclosee'

                    return parties
                else:
                    return parties
            else:
                return parties



    ##the parties name is 'identified below' or 'specified below' in other lines
    def partyIdentifyCase7(self, nlp, lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]

        parties = {}
        parties['party1'] = {}
        parties['party2'] = {}
        parties['party1']["FullName"] = ""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        startLine=None
        reverseReading=0
        reverseLine=None
        for i in range(len(lines)):
            if 'identified below' in lines[i] or 'specified below' in lines[i]:
                reverseReading=1
                reverseLine=i
                break


        for i in range(len(lines)):
            if lines[i].lower()=='parties:' or lines[i].lower()=='parties':
                startLine=i
                break


        temp=[]

        if reverseReading:
            if reverseLine!=None:
                for i in range(reverseLine+1):   #check the first ORG and its line before the reverseLine
                    # for i in range(len(lines)):
                    # print lines[i]
                    doc = nlp(unicode(lines[i], 'utf-8'))
                    wordAndLine = {}
                    for ent in doc.ents:
                        if ent.label_ == "ORG":
                            wordAndLine["word"] = ent.text
                            wordAndLine["line"] = i
                            temp.append(wordAndLine)
                        if len(temp)!=0:
                            break

                for i in reversed(range(reverseLine,len(lines))): # get ORG and its line reversely
                #for i in range(len(lines)):
                        #print lines[i]
                        doc = nlp(unicode(lines[i], 'utf-8'))
                        wordAndLine={}
                        for ent in doc.ents:
                            if ent.label_=="ORG":
                                wordAndLine["word"]=ent.text
                                wordAndLine["line"]=i
                                temp.append(wordAndLine)
        else:
            if startLine!=None:
                for i in range(startLine,len(lines)):
                #for i in range(len(lines)):
                        #print lines[i]
                        doc = nlp(unicode(lines[i], 'utf-8'))
                        wordAndLine={}
                        for ent in doc.ents:
                            if ent.label_=="ORG":
                                wordAndLine["word"]=ent.text
                                wordAndLine["line"]=i
                                temp.append(wordAndLine)



        if temp!=[]:

            line1=0
            line2=0
            for i in range(len(temp)):
                parties["party1"]["FullName"]=temp[i]["word"]
                line1=temp[i]["line"]
                break

            for i in range(len(temp)):
                if temp[i]["word"]==parties["party1"]["FullName"]:
                    continue
                else:
                    parties["party2"]["FullName"]=temp[i]["word"]
                    line2 = temp[i]["line"]
                    break

            key1=""
            key2=""

            keyPattern = re.compile("\((.*?)\)")

            for each in keyPattern.finditer(lines[line1]):
                    key1=each.group().replace(")","").replace("(","")

            for each in keyPattern.finditer(lines[line2]):
                key2 = each.group().replace(")","").replace("(","")


            doc1=nlp(unicode(lines[line1], 'utf-8'))
            doc2 = nlp(unicode(lines[line2], 'utf-8'))

            for ent in doc1.ents:
                if ent.label_=='ORG':
                    parties["party1"]["FullName"]=ent.text
                    break

            for ent in doc2.ents:
                if ent.label_=='ORG':
                    parties["party2"]["FullName"]=ent.text
                    break

            if not key1:
                parties["party1"]["ShortName"] = ""
                parties["party1"]["Role"] = "Discloser/Disclosee"
            else:
                if any(x in key1 for x in disclosureParty):
                    parties["party1"]["ShortName"] = ""
                    parties["party1"]["Role"] = "Discloser"
                else:

                    parties["party1"]["ShortName"] = key1
                    parties["party1"]["Role"] = "Discloser/Disclosee"

            if not key2:
                parties["party2"]["ShortName"] = ""
                parties["party2"]["Role"] = "Discloser/Disclosee"
            else:
                if any(x in key2 for x in receivingParty):
                    parties["party2"]["ShortName"] = ""
                    parties["party2"]["Role"] = "Disclosee"
                else:
                    parties["party2"]["ShortName"] = key2
                    parties["party2"]["Role"] = "Discloser/Disclosee"



            #print parties
            return parties
        else:
            return parties


    #Both two parties in the same sentence
    def partyIdentifyCase8(self, nlp, lines):

        disclosureParty = ["Discloser", "Supplier", "Provider", "Disclosing Party", "the Discloser",
                           "a Disclosing Party"]
        receivingParty = ["Receiving Party", "Recipient", "the Recipient", "RECIPIENT"]

        parties = {}
        parties['party1'] = {}
        parties['party2'] = {}
        parties['party1']["FullName"] = ""
        parties['party1']["ShortName"] = ""
        parties['party1']["Role"] = ""
        parties['party2']["FullName"] = ""
        parties['party2']["ShortName"] = ""
        parties['party2']["Role"] = ""

        line1 = None
        line2 = None


        for lineNubmer in range(len(lines)):
            if any(i in lines[lineNubmer] for i in disclosureParty):
                line1 = lineNubmer
            if line1 != None:
                break

        for lineNubmer in range(len(lines)):
            if any(i in lines[lineNubmer] for i in receivingParty):
                line2 = lineNubmer
            if line2 != None:
                break

        #two parties are in the same line
        if line1!=None and line2!=None and line1==line2:
            keys = []
            keyPattern = re.compile("\((.*?)\)")
            newLine=lines[line1]

            for each in keyPattern.finditer(newLine):
                key = {}
                if "ABN" in each.group() or "ACN" in each.group():
                    continue
                else:
                    key['key'] = each.group().replace(")", "").replace("(", "")
                    key['start'] = each.start()
                    key['end'] = each.end()
                    keys.append(key)


            doc = nlp(unicode(lines[line1], 'utf-8'))
            tempPartyNames=[]
            for ent in doc.ents:
                if ent.label_=='ORG':
                    tempPartyNames.append(ent.text)
            if len(tempPartyNames)==2:
                parties['party1']['FullName']=tempPartyNames[0]
                parties['party2']['FullName'] = tempPartyNames[1]
                parties['party1']['Role'] = keys[0]['key']
                parties['party2']['Role'] = keys[1]['key']

            return parties

        else:
            return parties

    def extractResult(self,parties):
        result=[]
        if parties['party1']['FullName']!='':
            result.append(parties['party1']['FullName'])

        if parties['party1']['Role'] != '':
            result.append(parties['party1']['Role'])

        if parties['party2']['FullName']!='':
            result.append(parties['party2']['FullName'])

        if parties['party2']['Role'] != '':
            result.append(parties['party2']['Role'])


        return result

    def partyIdentifier(self,nlp,lines):
        parties=self.partyIdentifyCase1(nlp,lines)
        if len(self.extractResult(parties))==4:
            print "case1"
            return parties
        else:
                parties=self.partyIdentifyCase2(nlp,lines)
                if len(self.extractResult(parties))==4:
                    print "case2"
                    return parties
                else:
                    parties = self.partyIdentifyCase3(nlp,lines)
                    print "case3"
                    print parties
                    if len(self.extractResult(parties)) == 4:
                        print "case3"

                        return parties
                    else:
                        parties = self.partyIdentifyCase4(nlp,lines)
                        if len(self.extractResult(parties)) == 4:
                            print "case4"
                            return parties
                        else:
                            parties = self.partyIdentifyCase5(nlp,lines)
                            if len(self.extractResult(parties)) == 4:
                                print "case5"
                                return parties
                            else:
                                parties = self.partyIdentifyCase6(nlp,lines)
                                print "case6"
                                if len(self.extractResult(parties)) == 4:

                                    return parties
                                else:
                                    parties = self.partyIdentifyCase7(nlp, lines)
                                    print "case7"
                                    if len(self.extractResult(parties)) == 4:
                                        return parties
                                    else:
                                        return parties

def extractLines(fileStream):
    abnPattern=re.compile("ABN \d+\s+\d+\s+\d+\s+\d+")
    acnPattern = re.compile("ACN \d+\s+\d+\s+\d+")
    lines=[]
    tempLines=fileStream.split("\n")

    for i in tempLines:
        if not i.strip():
            continue
        else:
            line=i.decode("unicode-escape").encode('utf-8').strip().replace("BETWEEN",'between').replace("AND","and")

            line = ' '.join(line.split())
            if "(ABN" in line or "(ACN" in line:
                lines.append(line)
            else:
                if "ABN" in line:

                    if abnPattern.finditer(line):
                        for each in abnPattern.finditer(line):
                            line=line.replace(each.group(),"("+each.group()+")")
                            lines.append(line)
                elif "ACN" in line:
                    if acnPattern.finditer(line):
                        for each in acnPattern.finditer(line):
                            line = line.replace(each.group(), "(" + each.group() + ")")
                            lines.append(line)
                else:
                    lines.append(line)
    return lines
def find_between(s, firstString, lastString):
    try:
        start = s.index(firstString ) + len(firstString)
        end = s.index(lastString, start )
        return firstString+s[start:end]+lastString
    except ValueError:
        return ""
def RemoveFromStartTo(s, String):
    try:
        end = s.index(String)
        return s[end:]
    except ValueError:
        return ""

#remove the string and everything before
def RemoveFromStartAfter(s, String):
    try:
        end = s.index(String)
        return s[end+len(String):]
    except ValueError:
        return ""