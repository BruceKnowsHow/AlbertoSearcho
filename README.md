# Overview

A search engine for CS 121 (search systems class) at University of California, Irvine.

# Usage
Inside of indexer.py, configure the corpus_folder. This should be the folder which contains all the downloaded web pages to be indexed over.

The index data will be stored in "Index/" of the current directory. The index is structured as a large "map.json" file, as well as many partition files named "i.json", where i is in the range(PARTITION_COUNT).
