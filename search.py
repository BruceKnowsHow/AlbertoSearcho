import sys
import json
import time
import math
from nltk.stem import *

index_file = 'index.json'

stemmer = PorterStemmer()

def token_freqs(tokens): # returns {token: count} dict of str->int
    ret = {}
    
    for token in tokens:
        if (token not in ret):
            ret[token] = 1
        else:
            ret[token] = ret[token] + 1
    
    return ret

def SparseDot(vec_dict1, vec_dict2):
    return sum((v * vec_dict2[k]) for k,v in vec_dict1.items() if k in vec_dict2)

def main():
    url_dict = {}
    with open('url_dict.json', 'r') as fp:
        url_dict = json.loads(fp.read())
    
    seek_dict = {}
    with open('seek_dict.json', 'r') as fp:
        seek_dict = json.loads(fp.read())
    
    N = len(url_dict)
    
    inverted_index = open(index_file, 'r')
    
    while True:
        print("Please enter a query")
        
        search_terms = [stemmer.stem(token) for token in input().lower().split()]
        
        start_time = time.time()
        
        freq_dict = token_freqs(search_terms)
        freq_dict = {k: freq_dict[k] for k in freq_dict.keys() & seek_dict.keys()}
        
        total_tf_idf = sum((1 + math.log10(v))**2 for v in freq_dict.values())**0.5
        
        docs = {}
        for k,v in freq_dict.items():
            inverted_index.seek(seek_dict[k])
            postings = json.loads(inverted_index.readline())
            
            v = (1 + math.log10(v)) * (math.log10(N / len(postings))) / total_tf_idf
            freq_dict[k] = v
            
            count = 0
            for posting in postings:
                if count > 1000: break
                count += 1
                if posting[0] not in docs:
                    docs[posting[0]] = {}
                
                docs[posting[0]][k] = posting[1]
        
        for k,v in docs.items():
            docs[k] = SparseDot(freq_dict, v)
        
        docs = sorted(docs.items(), key=lambda x: x[1], reverse=True)
        
        timeTaken = str(int((time.time() - start_time) * 1000))
        
        count = 0
        for doc in docs:
            if count > 10: break
            print(str(round(doc[1], 8)) + ': ' + url_dict[str(doc[0])])
            count += 1
        
        print()
        print("(Discovered " + str(len(docs)) + ' documents in ' + timeTaken + "ms)")
        

main()
