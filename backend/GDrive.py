import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.fs import GDriveFileSystem
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

from datetime import datetime

#from backend.utilities import timer

DEFAULT_GDRIVE_REMOTE_PATH = "root/saves/"
PATH_TO_CLIENT_CREDS = Path("./credentials/credentials.json")
PATH_TO_TOKENS = Path("./credentials/tokens.json")
SCOPES = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.metadata"
    ]


class GDrive:
    """A Class allowing manipulation of the GoogleDrive object

    TODO: Remove pydrive2 dependency by interacting directly with GDrive API.
    """

    def __init__(self):

        
        try:
            self.drive_service = self._get_auth_service()   
        except RefreshError as e:
            # Don't like this. Not sure why it sometimes throws a RefreshError when the token is expired.
            print(e)
            print("Deleting credentials and reauthenticating.")
            os.remove(PATH_TO_TOKENS)
            self.drive_service = self._get_auth_service()


        '''
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


    def upload_files(self, local_path, upload_path, game_name):
        upload_flag = True
        try:
            if self.file_exists(upload_path):
                if self.file_needs_update(local_path, game_name):
                    # This is probably not ideal since it is a destructive action.
                    self.__fs.rm(upload_path)
                    
                else:
                    upload_flag = False
                    print(f"{upload_path} already exists and is up to date.")
            if upload_flag:
                files = os.listdir(local_path)
                if [d for d in files if os.path.isdir(os.path.join(local_path, d))]:
                    files = [f for f in files if os.path.isfile(os.path.join(local_path, f))]
                    print(files)
                    for file in files:
                        self.__fs.put(f'{local_path}/{file}', f'{upload_path}/{file}', recursive=True, mkdir=True)

                else:
                    self.__fs.put(f'{local_path}/*', upload_path, recursive=True)
        except Exception as e:
            print(f"Error uploading files from {local_path} to {upload_path}: {e}")

    def upload_to_gdrive(
        self,
        local_path: str,
        game_name: str,
        remote_path: str = DEFAULT_GDRIVE_REMOTE_PATH,
    ) -> None:
        """Simple method to upload file to GDrive.

        
        TODO: There's an issue where put fails if there are subdirectories mixed with the files.
              Obvious solution is to iterate over each file and upload one by one. Really need
              to get rid of pydrive2 dependency.
        TODO: Ask users if they want to preserve old saves if they would be deleted otherwise

        """

        if remote_path == DEFAULT_GDRIVE_REMOTE_PATH:
            remote_path += game_name
            for root, dirs, files in os.walk(local_path):
                if files:
                    upload_path = remote_path + root.partition(local_path)[-1].replace('\\', '/')
                    self.upload_files(root, upload_path, game_name)



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

        return file_list[0]'''


    def _get_auth_service(self):
        '''Method for creating gdrive authentication service.'''
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
            with open(PATH_TO_TOKENS, 'w') as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    def get_folder_metadata(self, foldername: str) -> str or None:
        '''Returns folds id, name, and parents if it exists, else None.'''
        q = f"name = '{foldername}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false"

        response = self.drive_service.files().list(q=q, fields='files(id, name, parents)').execute()

        
        return response.get('files', [])[0] if response.get('files', []) else None
    
    def create_folder(self, foldername: str, parents: list = []) -> str:
        '''Method to create and upload a folder to GDrive.
        
           Returns the folder id if successful, else None.
        '''

        try:
            file_metadata = {'name': foldername,
                         'mimeType': 'application/vnd.google-apps.folder',
                         'parents': parents}

            file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            return 

        return file.get('id')

    def create_file(self, filename: str, parents: list = []) -> str:
        '''Method to create and upload a file to GDrive.
        
           Returns the file id if successful, else None.'''

        try:
            file_metadata = {'name': Path(filename).parts[-1],
                             'parents': parents}
            
            media = MediaFileUpload(filename)

            file = self.drive_service.files().create(uploadType='multipart', body=file_metadata, media_body=media, fields='id').execute()
        except HttpError as error:
            print(f'An error occurred: {error}')
            return 
        return file.get('id')

    def upload_files(self, local_path: str):
        '''Method for uploading all contents of given path.'''

        seen_folders = {}
        for path, _, files in os.walk(local_path):
            parts = Path(path).parts
            folder_name = parts[-1]
            if parts[-1] not in seen_folders:
                res = self.get_folder_metadata(folder_name)
                if not res:
                    parents = seen_folders.get(parts[-2]) if len(parts) > 1 else []

                    file_id = self.create_folder(folder_name, parents)
                    seen_folders[folder_name] = [file_id]

                else:
                    parents = res['parents']
                    seen_folders[folder_name] = parents
            for file in files:
                self.create_file(f'{path}/{file}', seen_folders[folder_name])

                    
    
if __name__ == '__main__':
    gdrive = GDrive()
    gdrive.test_upload('.')


