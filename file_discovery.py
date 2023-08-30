
import os
import re
import json


def save_discovered_folders_to_json(discovered_folders: dict) -> int:
    with open('./data/discovered_folders.json', 'w', encoding='utf-8') as f:
        json.dump(discovered_folders, f, ensure_ascii=False)

    return 1


def load_discovered_folders_from_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        discovered_folders = json.load(f)

    return discovered_folders

def discover_folders(path: str) -> int:

    discovered_folders = load_discovered_folders_from_json('./data/discovered_folders.json')
    
    
    for root, dirs, files in os.walk(path):
        matching = [dir for dir in dirs if re.search(r'^save|^Save', dir)]
        if matching:
            game_name = re.search("(?<=common[\\\]).*(?=\\\)|(?<=common[\\\]).*", root)[0]
            if game_name not in discovered_folders:
                for match in matching:
                    
                    discovered_folders[game_name] = os.path.join(root, match)

    save_discovered_folders_to_json(discovered_folders)
    
    return 1

if __name__ == '__main__':
    
    path = 'C:\Program Files (x86)\Steam\steamapps\common'

    discover_folders(path)
            