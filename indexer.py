from bs4 import BeautifulSoup
import os
import json
import re
from collections import defaultdict
import time
import shutil
import ijson
import glob

corpus_folder = os.path.join(os.getcwd(), 'developer')
index_folder = os.path.join(os.getcwd(), 'index')

if (os.path.exists(index_folder)):
	shutil.rmtree(index_folder)
os.makedirs(index_folder)

MAX_DOCUMENTS = 100000
DOCS_PER_FRAGMENT = 100000

start_time = time.time()

def tokenize(text):
	text = re.sub('[^A-Za-z0-9]+', ' ', text)
	
	return text.lower().split()

def token_freqs(tokens): # returns {token: count} dict of str->int
	ret = {}
	
	for token in tokens:
		if (token not in ret):
			ret[token] = 1
		else:
			ret[token] = ret[token] + 1
	
	return ret

def BuildIndexFragments(corpus_folder):
	inverted_index = defaultdict(lambda: [])
	url_dict = {}
	
	frag_id = 0
	doc_id = 0
	for filename in glob.iglob(corpus_folder + '/**/*.json', recursive=True):
		filetext = None
		with open(filename, 'r') as fp:
			filetext = fp.read()

		json_dict = json.loads(filetext)
		soup = BeautifulSoup(json_dict['content'], 'html.parser')
		text_tokens = tokenize(soup.text)
		
		freq_dict = token_freqs(text_tokens)
		
		for k,v in freq_dict.items():
			posting = [doc_id, v]    # THIS IS THE POSTING
			inverted_index[k].append(posting)
			url_dict[doc_id] = json_dict['url']
		
		if (doc_id % DOCS_PER_FRAGMENT == DOCS_PER_FRAGMENT - 1):
			with open(os.path.join(index_folder, 'fragment' + str(frag_id) + '.json'), 'w') as fp:
				json.dump(inverted_index, fp, indent=True)
			
			frag_id += 1
			inverted_index = defaultdict(lambda: [])
		
		print('\rProcessing document number: ' + str(doc_id) + ', seconds: ' + str(time.time() - start_time), end='')
		doc_id += 1
		if (doc_id >= MAX_DOCUMENTS):
			break
	
	if (doc_id % DOCS_PER_FRAGMENT != DOCS_PER_FRAGMENT - 1):
		with open(os.path.join(index_folder, 'fragment' + str(frag_id) + '.json'), 'w') as fp:
			json.dump(inverted_index, fp, indent=True)
	
	print('\nSaved ' + str(frag_id+1) + ' inverted index fragments.')
	
	with open('url_dict.json', 'w') as fp:
		json.dump(url_dict, fp, indent=True)
	print('\nSaved url_dict.json')
	
	return inverted_index, url_dict

def main():
	inverted_index, url_dict = BuildIndexFragments(corpus_folder)
	
	with open('index.json', 'w') as fp:
		json.dump(inverted_index, fp, indent=True)
	
	# frag_list = []
	# for filename in glob.iglob(index_folder + '/*.json'):
	# 	frag_list.append(ijson.items(open(filename, 'r'), ''))
	# 
	# print(frag_list[0].items)

main()
