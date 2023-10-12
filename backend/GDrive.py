import os
from pydrive2.auth import GoogleAuth, RefreshError
from pydrive2.drive import GoogleDrive
from pydrive2.fs import GDriveFileSystem
from pathlib import Path

from datetime import datetime

import concurrent.futures
import threading

from backend.utilities import timer

DEFAULT_GDRIVE_REMOTE_PATH = "root/saves/"
PATH_TO_TOKENS = Path("./credentials/tokens.json")


class GDrive:
    """A Class allowing manipulation of the GoogleDrive object

    TODO: Remove pydrive2 dependency by interacting directly with GDrive API.
    """

    def __init__(self):
        self.__gauth = GoogleAuth()
        self.__gauth.LoadCredentialsFile(PATH_TO_TOKENS)
        try:
            if not self.__gauth:
                self.__gauth.LocalWebserverAuth()
            elif self.__gauth.access_token_expired:
                self.__gauth.Refresh()
            else:
                self.__gauth.Authorize()
        except RefreshError as e:
            # Don't like this. Not sure why it sometimes throws a RefreshError when the token is expired.
            print(e)
            print("Deleting credentials and reauthenticating.")
            os.remove(PATH_TO_TOKENS)
            self.__gauth.credentials = None
            self.__gauth.LocalWebserverAuth()
        self.__drive = GoogleDrive(self.__gauth)
        self.__fs = GDriveFileSystem("root", google_auth=self.__gauth)
        self.upload_event = threading.Event()


    def upload_files(self, local_path, upload_path, game_name):
        try:
            if self.file_exists(upload_path):
                print('HI')
                if self.file_needs_update(local_path, game_name):
                    print('hello')
                    # This is probably not ideal since it is a destructive action.
                    self.__fs.rm(upload_path)
                    self.__fs.put(f'{local_path}/*', upload_path, recursive=True)
                else:
                    print(f"{upload_path} already exists and is up to date.")
            else:
                print('goodbye')
                self.__fs.put(f'{local_path}/*', upload_path, recursive=True)
        except Exception as e:
            print(f"Error uploading files from {local_path} to {upload_path}: {e}")
        finally:
            self.upload_event.set()

    def upload_to_gdrive(
        self,
        local_path: str,
        game_name: str,
        remote_path: str = DEFAULT_GDRIVE_REMOTE_PATH,
    ) -> None:
        """Simple method to upload file to GDrive.

        TODO: Maybe handle uploading entire folders.
        TODO: Ask users if they want to preserve old saves if they would be deleted otherwise

        """

        if remote_path == DEFAULT_GDRIVE_REMOTE_PATH:
            remote_path += game_name
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for root, dirs, files in os.walk(local_path):
                if files:
                    upload_path = remote_path + root.partition(local_path)[-1].replace('\\', '/')
                    executor.submit(self.upload_files, root, upload_path, game_name)
                    self.upload_event.wait()

        self.upload_event.clear()


    def download_from_g_drive(
        self,
        remote_path: str,
        game_name: str,
        local_path: str,
    ) -> None:
        """Simple method to download backups from GDrive.

        TODO: Make this work with linux if it doesn't already.
        TODO: Give user option to download even if remote is older than local.
        """
        if self.file_exists(local_path, local=True):
            if self.file_needs_update(local_path, game_name, download=True):
                # I'm leaving recursive=True here in case I want this to work for folders.
                self.__fs.get(remote_path, local_path, recursive=True)
                print(f"{remote_path} copied to {local_path}.")
            else:
                # We'll eventually give the user the option to download even if remote is older.
                print(f"{local_path} is more recent than {remote_path}.")
        else:
            self.__get(remote_path, local_path, recursive=True)

    def file_needs_update(
        self,
        local_path: str,
        game_name: str,
        download=False,
    ) -> bool:
        
        metadata = self.get_metadata(game_name)
        print('checked')
        local_modified_time = datetime.fromtimestamp(
            os.path.getmtime(local_path)
        ).isoformat()
        remote_modified_time = metadata["modifiedDate"]

        if not download:
            return local_modified_time > remote_modified_time
        else:
            return remote_modified_time > local_modified_time

    def file_exists(
        self,
        path: str,
        local=False,
    ) -> bool:
        """Simple method to check if the file exists remotely"""
        if not local:
            return self.__fs.exists(path)
        else:
            os.path.isfile(path)

    def get_metadata(self, game_name: str) -> dict:
        """Method to retrieve metada for a file in the user's GDrive."""
        
        q = {"q": f'title = "{game_name}" and trashed=False'}

        file_list = self.__drive.ListFile(q).GetList()

        return file_list[0]
