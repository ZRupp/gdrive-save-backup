import os
import re
import json
import sys

sys.path[0] += "\\.."
from json.decoder import JSONDecodeError
from backend.utilities import load_from_json, save_to_json
from backend.GDrive import GDrive
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

# Maybe we should use SQL instead of saving to json. Would allow saving date backed up.
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


def discover_folders(paths_to_process: list) -> None:
    """Method to discover location of save files. Currently only seeks steam save data in Windows.

    TODO:   - Make OS agnostic
            - Error Handling
    """
    discovered_folders = load_from_json(DISCOVERED_FOLDERS_PATH)

    for path in paths_to_process:
        for root, dirs, files in os.walk(path):
            dirs[:] = set(dirs) - EXCLUDED_FOLDERS - set(discovered_folders)
            matching = [dir for dir in dirs if re.search(r"^save", dir, re.IGNORECASE)]
            if matching:
                dirs[:] = []
                print(f"{root}{matching}")
                if "common" in root:
                    re_query = "(?<=common[\\\]).*(?=\\\)|(?<=common[\\\]).*"

                    # TODO: Things can possibly go wrong here if there is no match!!!
                    game_name = re.search(re_query, root)[0]
                else:
                    game_name = root.split(os.path.sep)[-1]

                discovered_folders[game_name] = f"{root}/{matching[0]}"

    save_to_json(discovered_folders, DISCOVERED_FOLDERS_PATH)


def discover_steam_libraries() -> list:
    """Method for discovering Steam libraries on all drives using default SteamLibrary naming convention."""

    drive_letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    game_install_location = "SteamLibrary/steamapps/common"
    default_install_location = "Program Files (x86)/Steam/steamapps/common"

    return [
        f"{drive}:/{game_install_location if drive != 'C' else default_install_location}"
        for drive in drive_letters
        if os.path.exists(
            f"{drive}:{game_install_location if drive != 'C' else default_install_location}"
        )
    ]


def generate_paths() -> list:
    paths = PC_DEFAULT
    paths += STEAM_PATH

    paths += discover_steam_libraries()

    discover_folders(paths)

    return paths


if __name__ == "__main__":
    paths = PC_DEFAULT
    paths += STEAM_PATH

    paths += discover_steam_libraries()

    discover_folders(paths)

    print(load_from_json(DISCOVERED_FOLDERS_PATH))
    """
    drive = g_drive.GDrive()
"""
    discovered_folders = load_from_json(DISCOVERED_FOLDERS_PATH)

    print(discovered_folders)

    for game_name, folder in discovered_folders.items():
        print(folder)
        for root, dirs, files in os.walk(folder):
            print(root, dirs, files)
            """for file in files:
                drive.upload_to_g_drive(
                    f"{folder}\\{file}", f"{REMOTE_SAVE_PATH}{game_name}/{file}"
                )

        # drive.upload_to_g_drive(folder + "/*", f"{REMOTE_SAVE_PATH}{game_name}/")
"""
