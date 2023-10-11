import os
import re
import sys

sys.path[0] += "\\.."
from backend.utilities import load_from_json, save_to_json
import pathlib

import concurrent.futures
import threading

json_lock = threading.Lock()

# Don't really like this, but we'll figure out a better solution later
# Maybe save these to a configuration file in json?
STEAM_PATH = [pathlib.Path("C:/Program Files (x86)/Steam/steamapps/common")]
PC_DEFAULT = [
    pathlib.Path("~/AppData").expanduser(),
    pathlib.Path("~/Documents/SavedGames").expanduser(),
    pathlib.Path("~/SavedGames").expanduser(),
]

REMOTE_SAVE_PATH = "root/saves/"

# Maybe we should use SQL instead of saving to json. Would allow saving date backed up.
DISCOVERED_FOLDERS_PATH = pathlib.Path("./data/discovered_folders.json")
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

def discover_folders_parallel(paths_to_process: list) -> None:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit the discover_folders function for each path to process
        results = [executor.submit(discover_folders, path) for path in paths_to_process]

        # Wait for all tasks to complete
        concurrent.futures.wait(results)

    joined_results = {}
    
    for result in results:
        joined_results.update(result.result())

    save_to_json(joined_results, DISCOVERED_FOLDERS_PATH)

def discover_folders(path: str) -> None:
    """Method to discover location of save files. Currently only seeks steam save data in Windows.

    TODO:   - Make OS agnostic
            - Error Handling
    """
    with json_lock:
        discovered_folders = load_from_json(DISCOVERED_FOLDERS_PATH)


    discovered_paths = set(discovered_folders.values())
    discovered_game_names = set(discovered_folders)


    for root, dirs, files in os.walk(path):
        if root.count(os.sep) > 15:
            dirs[:] = []
        else:
            dirs[:] = set(dirs) - EXCLUDED_FOLDERS - discovered_game_names
            matching = [dir for dir in dirs if dir.lower().startswith('save')]
            if matching:
                save_path = f"{root}/{matching[0]}"
                dirs[:] = []
                
                if len(os.listdir(save_path)) > 0 and str(
                    pathlib.Path(save_path)
                ) not in discovered_paths:
                    p = pathlib.Path(root)

                    if "common" in root:
                        game_name = p.parts[p.parts.index("common") + 1]
                    else:
                        game_name = p.parts[-1]

                    discovered_folders[game_name] = str(pathlib.Path(save_path))

    return discovered_folders


def discover_steam_libraries() -> list:
    """Method for discovering Steam libraries on all drives using default SteamLibrary naming convention."""

    drive_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    game_install_location = "SteamLibrary/steamapps/common"
    default_install_location = "Program Files (x86)/Steam/steamapps/common"

    return [
        pathlib.Path(
            f"{drive}:/{game_install_location if drive != 'C' else default_install_location}"
        )
        for drive in drive_letters
        if os.path.exists(
            f"{drive}:{game_install_location if drive != 'C' else default_install_location}"
        )
    ]


def generate_paths() -> list:
    """Simple method to build list of paths for PC"""
    paths = PC_DEFAULT
    paths += STEAM_PATH

    paths += discover_steam_libraries()

    return paths


def start_discovery():
    """Begins the save discovery process"""

    print("Generating paths...")
    paths = generate_paths()
    print("Discovering saves...")
    discover_folders_parallel(paths)
    print("Done!")
