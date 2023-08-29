
from os import scandir, walk
import re


if __name__ == '__main__':
    
    cadidates = []
    
    for root, dirs, files in walk('C:\Program Files (x86)\Steam\steamapps\common'):
        matching = [dir for dir in dirs if re.search(r'save|Save', dir)]
        if matching:
            print(root, matching, dirs)
            