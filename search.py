import sys
import json
import time

index_file = 'index.json'

url_dict = {}
with open('url_dict.json', 'r') as fp:
    url_dict = json.loads(fp.read())

def main():
    inverted_index = {}
    with open(index_file, 'r') as fp:
        inverted_index = json.loads(fp.read())
    
    print("Please enter a query")
    
    search_terms = input().split()
    
    start_time = time.time()
    
    rows = []
    for term in search_terms:
        if term not in inverted_index:
            print("No results.")
            quit()
        
        rows.append(inverted_index[term])
    
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
