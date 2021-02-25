from pycorenlp import StanfordCoreNLP

Stanford_nlp = StanfordCoreNLP('http://localhost:9000')

def StanfordRSParser(sentence):
    if type(sentence) != str:
        sentence=str(sentence)
    output = Stanford_nlp.annotate(sentence, properties={
    'annotators': 'parse',
    'outputFormat': 'json'
    })
    return output['sentences'][0]['parse']
