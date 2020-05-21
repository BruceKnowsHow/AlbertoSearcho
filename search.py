import sys
import json
import time

index_file = 'index.json'

def main():
    url_dict = {}
    with open('url_dict.json', 'r') as fp:
        url_dict = json.loads(fp.read())
    
    seek_dict = {}
    with open('seek_dict.json', 'r') as fp:
        seek_dict = json.loads(fp.read())
    
    
    inverted_index = open(index_file, 'r')
    
    print("Please enter a query")
    
    search_terms = input().lower().split()
    
    start_time = time.time()
    
    rows = []
    for term in search_terms:
        if term not in seek_dict:
            print("No results.")
            quit()
        
        inverted_index.seek(seek_dict[term])
        
        row = json.loads(inverted_index.readline())
        
        rows.append(row)
    
    for row in rows[1:]:
        for elem0 in rows[0]:
            found = False
            
            for elem1 in row:
                if (elem0[0] == elem1[0]):
                    found = True
                    break
            
            if (not found):
                rows[0].remove(elem0)
    
    for elem in rows[0]:
        print(url_dict[str(elem[0])])
    
    print()
    print("(Response time: " + str(int((time.time() - start_time) * 1000)) + "ms)")
    

main()
