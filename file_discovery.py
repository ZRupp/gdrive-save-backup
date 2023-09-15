import os
import re
import json
from json.decoder import JSONDecodeError
import g_drive
import multiprocessing
import time

# Don't really like this, but we'll figure out a better solution later
# Maybe save these to a configuration file in json?
STEAM_PATH = ["C:/Program Files (x86)/Steam/steamapps/common"]
PC_DEFAULT = [
    os.path.expanduser("~/AppData"),
    os.path.expanduser("~/Documents/SavedGames"),
    os.path.expanduser("~/SavedGames"),
]

REMOTE_SAVE_PATH = "root/saves/"
DISCOVERED_FOLDERS_PATH = "./data/discovered_folders.json"
EXCLUDED_FOLDERS = set(
    [
        "Python",
        "Unity",
        "Yarn",
        "UnrealEngine",
        "EOSUserHelper",
        "CrashReportClient",
        "EpicGamesLauncher",
    ]
)


def save_discovered_folders_to_json(discovered_folders: dict) -> int:
    """Simple method for saving discovered folders in json format.

    returns int for success status

    TODO: - Error Handling
    """

    with open(DISCOVERED_FOLDERS_PATH, "w", encoding="utf-8") as f:
        json.dump(discovered_folders, f, ensure_ascii=False)

    return 1


def load_discovered_folders_from_json(path: str) -> dict:
    """Simple method for a json file populated with games and the save folder locations.

    returns a dict in the form {'game_name': 'path_to_game'}

    TODO:   - Either in this method or another, ensure that folders exist and remove
              them if not.
            - Error Handling
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            discovered_folders = json.load(f)
    except JSONDecodeError:
        print("Error reading `discovered_folders.json`. Starting over with blank file.")
        discovered_folders = {}

    return discovered_folders


def discover_folders_test(paths_to_process: list) -> None:
    """Method to discover location of save files. Currently only seeks steam save data in Windows.

    TODO:   - Make OS agnostic
            - Error Handling
    """
    discovered_folders = load_discovered_folders_from_json(DISCOVERED_FOLDERS_PATH)

    for path in paths_to_process:
        for root, dirs, files in os.walk(path):
            dirs[:] = set(dirs) - EXCLUDED_FOLDERS - set(discovered_folders)
            matching = [dir for dir in dirs if re.search(r"^save", dir, re.IGNORECASE)]
            if matching:
                dirs[:] = []
                print(f"{root}{matching}")
                if "common" in root:
                    re_query = "(?<=common[\\\]).*(?=\\\)|(?<=common[\\\]).*"
                    game_name = re.search(re_query, root)[0]
                else:
                    game_name = root.split(os.path.sep)[-1]

                discovered_folders[game_name] = matching

    save_discovered_folders_to_json(discovered_folders)


if __name__ == "__main__":
    paths = PC_DEFAULT
    paths += STEAM_PATH

    discover_folders_test(paths)

    print(load_discovered_folders_from_json(DISCOVERED_FOLDERS_PATH))
    """
    drive = g_drive.GDrive()

    discovered_folders = load_discovered_folders_from_json(DISCOVERED_FOLDERS_PATH)

    print(discovered_folders)

    for game_name, folder in discovered_folders.items():
        for root, dirs, files in os.walk(folder):
            print(root, dirs, files)
            for file in files:
                drive.upload_to_g_drive(
                    f"{folder}\\{file}", f"{REMOTE_SAVE_PATH}{game_name}/{file}"
                )

        # drive.upload_to_g_drive(folder + "/*", f"{REMOTE_SAVE_PATH}{game_name}/")
"""
