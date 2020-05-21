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

MAX_DOCUMENTS = 1000
DOCS_PER_FRAGMENT = 100

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

def IndexToText(inverted_index):
	ret = ""
	
	for k, v in sorted(inverted_index.items(), reverse=True):
		ret = ret + '["' + str(k) + '",' + str(v).replace(' ', '') + ']\n'
	
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
		text_tokens = tokenize(soup.text)
		
		freq_dict = token_freqs(text_tokens)
		
		for k,v in freq_dict.items():
			posting = [doc_id, v]    # THIS IS THE POSTING
			inverted_index[k].append(posting)
			url_dict[doc_id] = json_dict['url']
		
		if (doc_id % DOCS_PER_FRAGMENT == DOCS_PER_FRAGMENT - 1):
			with open(os.path.join(index_folder, 'fragment' + str(frag_id) + '.json'), 'w') as fp:
					fp.write(IndexToText(inverted_index))
			
			frag_id += 1
			inverted_index.clear()
		
		print('\rProcessing document number: ' + str(doc_id) + ', seconds: ' + str(time.time() - start_time), end='')
		doc_id += 1
		if (doc_id >= MAX_DOCUMENTS):
			break
	
	if (inverted_index):
		with open(os.path.join(index_folder, 'fragment' + str(frag_id) + '.json'), 'w') as fp:
			fp.write(IndexToText(inverted_index))
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
	
	while (all([line != '' for line in curr_lines])):
		curr_phrases = [json.loads(l) for l in curr_lines]
		curr_phrase = sorted(curr_phrases, key=lambda x: x[0], reverse=True)[0][0]
		active = [phrase[0] == curr_phrase for phrase in curr_phrases]
		
		line = []
		for i in range(len(active)):
			if (not active[i]): continue
			
			line = line + (curr_phrases[i][1])
			
			curr_lines[i] = files[i].readline()
		
		seek_dict[curr_phrase] = index_file.tell()
		
		# index_file.write(IndexToText({curr_phrase:line}))
		index_file.write(str(line).replace(' ', '') + '\n')
		
		print('\rProcessed phrase: ' + str(phrase_count) + ', seconds: ' + str(time.time() - start_time), end='')
		phrase_count += 1
	
	with open('seek_dict.json', 'w') as fp:
		json.dump(seek_dict, fp, indent=True)\

main()
