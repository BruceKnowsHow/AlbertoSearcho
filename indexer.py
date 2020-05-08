from bs4 import BeautifulSoup
import nltk
import os
import json
import re
from collections import defaultdict
import time

corpus_folder = os.path.join(os.getcwd(), 'developer')
index_folder = os.path.join(os.getcwd(), 'Index')

partition_mapfile = os.path.join(index_folder, 'map.json')

PARTITION_COUNT = 100
ACTIVE_PARTITIONS = 100

start_time = time.time()

class InvertedIndex:
	def __init__(self, partition_map={}, partitions=PARTITION_COUNT, max_active_partitions=ACTIVE_PARTITIONS):
		self.partitions = partitions
		self.partition_map = partition_map
		
		self.max_active_partitions = max_active_partitions
		self.loaded = []
		
		self.index = [{} for i in range(self.partitions)]
		
		for i in range(PARTITION_COUNT):
			for k in [k for k, v in self.partition_map.items() if v == i]:
				self.index[i][k] = []
			with open(os.path.join(index_folder, str(i) + '.json'), 'w') as fp:
				json.dump(self.index[i], fp, indent=True)
		
	
	def unload_partition(self, id):
		if (id not in self.loaded):
			return
		
		self.loaded.remove(id)
		
		with open(os.path.join(index_folder, str(id) + '.json'), 'w') as fp:
			json.dump(self.index[id], fp, indent=True)
		
		self.index[id] = None
	
	def load_partition(self, id):
		if (id in self.loaded):
			self.loaded.remove(id)
			self.loaded.insert(0, id)
			return
		
		if (len(self.loaded) > self.max_active_partitions):
			print('loading', id)
			self.unload_partition(self.loaded[-1])
		
		self.loaded.insert(0, id)
		
		with open(os.path.join(index_folder, str(id) + '.json'), 'r') as fp:
			self.index[id] = json.load(fp)
	
	def get_partition(self, partition):
		self.load_partition(partition)
		return self.index[partition]
	
	def set_partition(self, partition, value):
		self.load_partition(partition)
		self.index[partition] = value
	
	def __getitem__(self, key):
		self.load_partition(self.partition_map[key])
		return self.index[self.partition_map[key]][key]
	
	def __setitem__(self, key, value):
		self.load_partition(self.partition_map[key])
		self.index[self.partition_map[key]][key] = value

def tokenize(text):
	text = re.sub('[^A-Za-z0-9]+', ' ', text)
	
	return [token for token in text.lower().split() if (len(token) > 2 and (not token.isnumeric() or len(token) <= 6))]

def token_freqs(tokens): # returns {token: count} dict of str->int
	ret = {}
	
	for token in tokens:
		if (token not in ret):
			ret[token] = 1
		else:
			ret[token] = ret[token] + 1
	
	return ret

def build_partition_map():
	partition_map = {}
	doc_count = 0
	total_tokens = 0
	total_docs_dict = defaultdict(int)
	all_freqs_dict = defaultdict(int)
	
	try:
		with open(partition_mapfile, 'r') as fp:
			partition_map = json.load(fp)
		print('Found partition map file on disk, re-using', partition_mapfile, end='')
		return partition_map
	except FileNotFoundError:
		pass
	
	for directory, subdirectories, files in os.walk(corpus_folder):
		for file in files:
			filename = os.path.join(directory, file)

			if not filename.endswith('.json'):
				continue
			
			filetext = None
			with open(filename, 'r') as fp:
				filetext = fp.read()

			json_dict = json.loads(filetext)
			soup = BeautifulSoup(json_dict['content'], 'html.parser')
			text_tokens = tokenize(soup.text)
			
			# total_tokens += len(text_tokens)
			
			for k, v in token_freqs(text_tokens).items():
				total_docs_dict[k] += 1
				all_freqs_dict[k] += v
			
			total_tokens += len(token_freqs(text_tokens).items())
			
			print('\rProcessing document number: ' + str(doc_count) + ', unique tokens so far: ' + str(len(all_freqs_dict)) + ', seconds: ' + str(time.time() - start_time), end='')
			
			doc_count += 1
			if (doc_count > 1000):
				break
		else:
			continue
		break
	
	ordered = {k: v for k, v in sorted(total_docs_dict.items(), key=lambda item: item[1], reverse=True)}
	
	i = 0
	partition = 0
	for k,v in ordered.items():
		partition_map[k] = partition
		i += v
		if (i > total_tokens / PARTITION_COUNT):
			i = 0
			partition += 1
	
	with open(partition_mapfile, 'w') as fp:
		json.dump(partition_map, fp, indent=True)
	
	return partition_map

def main():
	print('Building partition map')
	partition_map = build_partition_map()
	print('\nFinished building partition map.\n')
	
	print('Building inverted index.')
	
	myindex = InvertedIndex(partition_map=partition_map)
	
	doc_count = 0
	for directory, subdirectories, files in os.walk(corpus_folder):
		for file in files:
			filename = os.path.join(directory, file)

			if not filename.endswith('.json'):
				continue
			
			filetext = None
			with open(filename, 'r') as fp:
				filetext = fp.read()

			json_dict = json.loads(filetext)
			soup = BeautifulSoup(json_dict['content'], 'html.parser')
			text_tokens = tokenize(soup.text)
			
			freq_dict = token_freqs(text_tokens)
			
			for k,v in freq_dict.items():
				id = partition_map[k]
				store_object = [doc_count, json_dict['url'], v]
				myindex[k].append(store_object)
			
			print('\rProcessing document number: ' + str(doc_count) + ', seconds: ' + str(time.time() - start_time), end='')
			doc_count += 1
			if (doc_count > 1000):
				break
		else:
			continue
		break
	
	print('\nFinished building inverted index.')
	
	for i in range(PARTITION_COUNT):
		myindex.unload_partition(i)
	
	print('Saved all index partitions to ' + index_folder)
	

main()
