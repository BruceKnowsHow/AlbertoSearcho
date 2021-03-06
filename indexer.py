from bs4 import BeautifulSoup
import os
import json
import re
from collections import defaultdict
import time
import shutil
import glob
import math
from nltk.stem import *

corpus_folder = os.path.join(os.getcwd(), 'developer')
index_folder = os.path.join(os.getcwd(), 'index')

MAX_DOCUMENTS = 100000
DOCS_PER_FRAGMENT = 500

start_time = time.time()

stemmer = PorterStemmer()
def tokenize(text):
	text = re.sub('[^A-Za-z0-9]+', ' ', text)
	
	return [stemmer.stem(token) for token in text.lower().split()]

def token_freqs(tokens): # returns {token: count} dict of str->int
	ret = {}
	
	for token in tokens:
		if (token not in ret):
			ret[token] = 1
		else:
			ret[token] = ret[token] + 1
	
	return ret

def WriteIndexFragment(inverted_index, filename):
	with open(filename, 'w') as fp:
		for k, v in sorted(inverted_index.items(), reverse=True):
			fp.write('["' + str(k) + '",' + str(v).replace(' ', '') + ']\n')

def GetBoosterText(soup):
	ret = []
	
	if (soup.title and soup.title.string): ret = ret + (tokenize(soup.title.string)) * 5
	if (soup.h1 and soup.h1.string): ret = ret + (tokenize(soup.h1.string)) * 4
	if (soup.h2 and soup.h2.string): ret = ret + (tokenize(soup.h2.string)) * 4
	if (soup.h3 and soup.h3.string): ret = ret + (tokenize(soup.h3.string)) * 3
	if (soup.h4 and soup.h4.string): ret = ret + (tokenize(soup.h4.string)) * 3
	if (soup.b and soup.b.string): ret = ret + (tokenize(soup.b.string)) * 2
	if (soup.strong and soup.strong.string): ret = ret + (tokenize(soup.strong.string)) * 2
	
	return ret

def BuildIndexFragments(corpus_folder):
	if (os.path.exists(index_folder)):
		shutil.rmtree(index_folder)
	os.makedirs(index_folder)
	
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
		text_tokens = tokenize(soup.text) + GetBoosterText(soup)
		
		freq_dict = token_freqs(text_tokens)
		
		total_tf = sum((1 + math.log10(v))**2 for v in freq_dict.values())**0.5
		
		for k,v in freq_dict.items():
			v = round((1 + math.log10(v)) / total_tf, 9)
			posting = [doc_id, v]    # THIS IS THE POSTING
			inverted_index[k].append(posting)
			url_dict[doc_id] = json_dict['url']
		
		if (doc_id % DOCS_PER_FRAGMENT == DOCS_PER_FRAGMENT - 1):
			fragname = os.path.join(index_folder, 'fragment' + str(frag_id) + '.json')
			WriteIndexFragment(inverted_index, fragname)
			
			frag_id += 1
			inverted_index.clear()
		
		print('\rProcessing document number: ' + str(doc_id) + ', seconds: ' + ('%.2f' % (time.time() - start_time)), end='')
		doc_id += 1
		if (doc_id >= MAX_DOCUMENTS):
			break
	
	if (inverted_index):
		fragname = os.path.join(index_folder, 'fragment' + str(frag_id)) + '.json'
		WriteIndexFragment(inverted_index, fragname)
		inverted_index.clear()
	
	print('\nSaved ' + str(frag_id+1) + ' inverted index fragments.')
	
	with open('url_dict.json', 'w') as fp:
		json.dump(url_dict, fp, indent=True)
	print('Saved url_dict.json')
	
	return

def main():
	BuildIndexFragments(corpus_folder)
	
	files = []
	for filename in glob.iglob(index_folder + '/*.json', recursive=True):
		files.append(open(filename, 'r'))
	
	curr_lines = [f.readline() for f in files]
	
	index_file = open('index.json', 'w')
	
	phrase_count = 0
	
	seek_dict = {}
	
	while any([line != '' for line in curr_lines]):
		curr_phrases = [json.loads(l) for l in curr_lines]
		curr_phrase = sorted(curr_phrases, key=lambda x: x[0], reverse=True)[0][0]
		active = [phrase[0] == curr_phrase for phrase in curr_phrases]
		
		line = []
		for i in range(len(active)):
			if (not active[i]): continue
			
			line = line + (curr_phrases[i][1])
			
			curr_lines[i] = files[i].readline()
		
		seek_dict[curr_phrase] = index_file.tell()
		
		line = sorted(line, key=lambda x: x[1], reverse=True)
		
		index_file.write(str(line).replace(' ', '') + '\n')
		
		print('\rProcessed phrase: ' + str(phrase_count) + ', seconds: ' + ('%.2f' % (time.time() - start_time)), end='')
		phrase_count += 1
	
	with open('seek_dict.json', 'w') as fp:
		json.dump(seek_dict, fp, indent=True)\

main()
