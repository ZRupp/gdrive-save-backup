import os
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from datetime import datetime, timezone

# from backend.utilities import timer

logging.basicConfig(
    filename="./logs/gdrive_log.log",
    format="%(asctime)s %(message)s",
    level=logging.INFO,
    filemode="w",
)
logger = logging.getLogger(__name__)

DEFAULT_GDRIVE_REMOTE_SAVE_FOLDER = "root/saves/"
PATH_TO_CLIENT_CREDS = Path("./credentials/credentials.json")
PATH_TO_TOKENS = Path("./credentials/tokens.json")
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.metadata",
]


class GDrive:
    """A Class allowing manipulation of the GoogleDrive object

    TODO: Remove pydrive2 dependency by interacting directly with GDrive API.
    """

    def __init__(self):
        try:
            self.drive_service = self._get_auth_service()
        except RefreshError as e:
            logger.error(f"Error during authentication: {e}")
            logger.info(f"Deleting {PATH_TO_TOKENS} and reauthenticating.")
            os.remove(PATH_TO_TOKENS)
            self.drive_service = self._get_auth_service()
        self.folder_ids = {'root': 'root'}
        self.initialize_folder_structure()

    def initialize_folder_structure(self):
        parts = Path(DEFAULT_GDRIVE_REMOTE_SAVE_FOLDER).parts
        for part in parts:
            existent_folder = self.get_folder_metadata(part)
            if part == 'root':
                folder_id = self.folder_ids['root']
            if not existent_folder:
                logger.info(f'Adding {part} to GDrive')
                folder_id = self.create_folder(part, [folder_id])
                self.folder_ids[part] = folder_id
            else:
                self.folder_ids[part] = self.get_folder_metadata(part)['id']
                print(self.folder_ids)

        '''
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
        '''

    def _get_auth_service(self):
        creds = None

        if os.path.exists(PATH_TO_TOKENS):
            creds = Credentials.from_authorized_user_file(PATH_TO_TOKENS, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    PATH_TO_CLIENT_CREDS, SCOPES
                )

                creds = flow.run_local_server()
            with open(PATH_TO_TOKENS, "w") as token:
                token.write(creds.to_json())

        return build("drive", "v3", credentials=creds)

    def get_folder_metadata(self, foldername: str) -> str or None:
        """Returns folder id, name, and parents if it exists, else None."""

        try:
            q = f"name = '{foldername}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false"

            response = (
                self.drive_service.files()
                .list(q=q, fields="files(id, name, parents)")
                .execute()
            )

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return

        return response.get("files", [])[0] if response.get("files", []) else None

    def get_file_metada(self, filename: str, parents: list) -> str or None:
        try:
            q = f"name = '{filename}' and trashed=false and '{parents[0]}' in parents"

            response = (
                self.drive_service.files()
                .list(q=q, fields="files(id, name, modifiedTime, parents)")
                .execute()
            )

        except HttpError or IndexError as error:
            logger.error(f"An error occurred: {error}")
            return

        return response.get("files", [])[0] if response.get("files", []) else None

    def create_folder(self, foldername: str, parents: list = []) -> str:
        """Method to create and upload a folder to GDrive.

        Returns the folder id if successful, else None.
        """

        try:
            file_metadata = {
                "name": foldername,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": parents,
            }

            file = (
                self.drive_service.files()
                .create(body=file_metadata, fields="id")
                .execute()
            )

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return

        return file.get("id")

    def create_file(self, filename: str, parents: list = []) -> str:
        """Method to create and upload a file to GDrive.

        Returns the file id if successful, else None."""

        try:
            file_metadata = {"name": Path(filename).parts[-1], "parents": parents}

            media = MediaFileUpload(filename)

            file = (
                self.drive_service.files()
                .create(
                    uploadType="multipart",
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                )
                .execute()
            )
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return
        return file.get("id")

    def update_file(self, local_file: str, remote_file_id: str) -> bool:
        """Method to update an existing file if the local file is newer than the remote file."""

        try:
            media = MediaFileUpload(local_file)

            file = (
                self.drive_service.files()
                .update(uploadType="multipart", media_body=media, fileId=remote_file_id)
                .execute()
            )
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return False
        return True
    
    def folder_processor(self, folder_name: str, parent_folder: str) -> str:
        existent_folder = self.get_folder_metadata(folder_name)
        if not existent_folder:
            current_folder_id = self.create_folder(folder_name, [parent_folder])
            self.folder_ids[folder_name] = current_folder_id

        else:
            current_folder_id = existent_folder["id"]
            self.folder_ids[folder_name] = current_folder_id
        
        return current_folder_id
    
    def file_processor(self, path: str, file: str, current_folder_id) -> str:
        file_path = f"{path}/{file}"
        existent_file = self.get_file_metada(file, [current_folder_id])

        if not existent_file:
            file_id = self.create_file(file_path, [current_folder_id])
        else:
            file_id = existent_file['id']
            local_modified_time = datetime.fromtimestamp(
                os.path.getmtime(file_path), tz=timezone.utc
            ).isoformat()
            remote_modified_time = existent_file["modifiedTime"]

            if local_modified_time > remote_modified_time:
                logger.info(f"{file_path} updating.")
                if self.update_file(file_path, existent_file.get("id")):
                    logger.info(f"{file_path} successfully updated.")
                else:
                    logger.info(f"{file_path} not updated.")
            else:
                logger.info(f"{file_path} already up-to-date.")
        
        return file_id

    def upload_files(self, local_path: str, game_name: str):
        """Method for uploading all contents of given path.

        TODO: Upload to Saves/game_name
        """
        top_folder = Path(local_path).parts[-1]
        # Make a folder for the game's saves
        existent_game_folder = self.get_folder_metadata(game_name)
        if not existent_game_folder:
            logger.info(f"{game_name} doesn't exist. Attempting to create.")
            # Get the parent id
            parent = self.folder_ids[Path(DEFAULT_GDRIVE_REMOTE_SAVE_FOLDER).parts[-1]]
            
            game_folder_id = self.create_folder(game_name, [parent]) 
            self.folder_ids[game_name] = game_folder_id
            logger.info(f'{game_name} folder created.')
        else:
            logger.info(f'{game_name} folder exists.')
            game_folder_id = existent_game_folder["id"]
            self.folder_ids[game_name] = game_folder_id
        current_folder_id = game_folder_id
        for path, _, files in os.walk(local_path):
            parts = Path(path).parts
            folder_name = parts[-1] if parts[-1] != top_folder else game_name
            logger.info(f'Processing {folder_name} folder.')
            current_folder_id = self.folder_processor(folder_name, current_folder_id)
            logger.info(f'Folder {folder_name} processed. Folder id is: {current_folder_id}.')

            for file in files:
                file_id = self.file_processor(path, file, current_folder_id)


if __name__ == "__main__":
    gdrive = GDrive()
    gdrive.upload_files("./test_upload/", "testytest")
    gdrive.drive_service.close()
