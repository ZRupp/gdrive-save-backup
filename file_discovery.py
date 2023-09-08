
import os
import re
import json
import g_drive

# Don't really like this, but we'll figure out a better solution later
STEAM_PATH = ['C:/Program Files (x86)/Steam/steamapps/common']
PC_DEFAULT = ['C:/Users']


def save_discovered_folders_to_json(discovered_folders: dict) -> int:
    '''Simple method for saving discovered folders in json format.

    returns int for success status

    TODO: - Error Handling
    '''

    with open('./data/discovered_folders.json', 'w', encoding='utf-8') as f:
        json.dump(discovered_folders, f, ensure_ascii=False)

    return 1


def load_discovered_folders_from_json(path: str) -> dict:
    '''Simple method for a json file populated with games and the save folder locations.

    returns a dict in the form {'game_name': 'path_to_game'}

    TODO:   - Either in this method or another, ensure that folders exist and remove
              them if not.
            - Error Handling  
    '''
    with open(path, 'r', encoding='utf-8') as f:
        discovered_folders = json.load(f)

    return discovered_folders

def discover_folders(path: str) -> int:
    '''Method to discover location of save files. Currently only seeks steam save data in Windows.

    returns success state as int

    TODO:   - Make OS agnostic
            - Discover folders for other launchers
                * Epic
                * Heroic
                * GOG
                * Others?
            - Discover folders in AppData and other common locations
            - Error Handling
    '''

    discovered_folders = load_discovered_folders_from_json('./data/discovered_folders.json') # Hard-coded value bad
    
    
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
    
    paths = STEAM_PATH

    for path in paths:
        discover_folders(path)

    drive = g_drive.GDrive()

    discovered_folders = load_discovered_folders_from_json('./data/discovered_folders.json')

    print(discovered_folders)

    for game_name, folder in discovered_folders.items():
        drive.upload_to_g_drive(folder +  '/*', f'root/saves/{game_name}/')
            