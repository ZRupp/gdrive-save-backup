import os
import io
import shutil
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
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
    def __init__(self):
        self.drive_service = self._get_auth_service()
        self.folder_ids = {"root": self._get_root_folder_id()}
        self.initialize_folder_structure()

    def __del__(self):
        logger.info("Closing drive service.")
        if self.drive_service:
            self.drive_service.close()
        logger.info("Drive service closed.")

    def _get_auth_service(self):
        try:
            creds = self._get_credentials()
        except RefreshError as e:
            logger.error(f"Error during authentication: {e}")
            logger.info("Deleting credentials and reauthenticating.")
            os.remove(PATH_TO_TOKENS)
            return self._get_auth_service()
        return build("drive", "v3", credentials=creds)

    def _get_credentials(self):
        creds = None
        if os.path.exists(PATH_TO_TOKENS):
            creds = Credentials.from_authorized_user_file(PATH_TO_TOKENS, SCOPES)
        if not creds or not creds.valid:
            creds = self._refresh_credentials(creds)
        return creds

    def _refresh_credentials(self, creds):
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                PATH_TO_CLIENT_CREDS, SCOPES
            )
            creds = flow.run_local_server()
            with open(PATH_TO_TOKENS, "w") as token:
                token.write(creds.to_json())
        return creds

    def _get_root_folder_id(self):
        return (
            self.drive_service.files().get(fileId="root", fields="id").execute()["id"]
        )

    def initialize_folder_structure(self):
        parts = Path(DEFAULT_GDRIVE_REMOTE_SAVE_FOLDER).parts
        parent = None
        for part in parts:
            if part == "root":
                folder_id = self.folder_ids["root"]
            else:
                parent = folder_id
                existent_folder = self.get_metadata(part, parent, type="folder")
                if not existent_folder:
                    logger.info(f"Adding {part} to GDrive")
                    folder_id = self.upload_to_gdrive(
                        part, parents=[folder_id], type="folder"
                    )
                    self.folder_ids[part] = folder_id
                else:
                    logger.info(f"{part} already exists.")
                    self.folder_ids[part] = existent_folder[0]["id"]

    def get_metadata(self, name: str=None, parent: str=None, type: str=None):
        try:
            q = 'trashed=false'
            if name:
                q += f" and name='{name}'"
            if parent:
                q += f" and '{parent}' in parents"
            if type == "folder":
                q += f" and mimeType = 'application/vnd.google-apps.folder'"

            response = (
                self.drive_service.files()
                .list(q=q, fields="files(id, name, modifiedTime, parents, mimeType)")
                .execute()
            )

        except HttpError or IndexError as error:
            logger.error(f"An error occurred: {error}")
            return

        return response.get("files", []) if response.get("files", []) else None

    def upload_to_gdrive(
        self,
        name: str,
        remote_file_id: str = None,
        parents: list = [],
        update: bool = False,
        type: str = "file",
    ) -> str:
        try:
            if not update:
                file_metadata = {"parents": parents}
                if type == "file":
                    file_metadata["name"] = Path(name).parts[-1]
                elif type == "folder":
                    file_metadata["name"] = name
                    file_metadata["mimeType"] = "application/vnd.google-apps.folder"

            media = MediaFileUpload(name) if type == "file" else None

            file_object = self.drive_service.files()

            if not update:
                file = file_object.create(
                    uploadType="multipart",
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                )
            else:
                file = file_object.update(
                    uploadType="multipart", media_body=media, fileId=remote_file_id
                )
            file = file.execute()

        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return
        return file.get("id")
    
    def download_file(self, file_id: str, save_path: str):
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}.")

        except HttpError as error:
            logger.info(f"An error occurred: {error}")
            file = None

        if file:
            file.seek(0)
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(file, f)

        return file.getvalue()
    
    def download_from_gdrive(self, parent_id: str, root_dir: str):
        children = self.get_metadata(parent=parent_id)
        for child in children:

            save_path = Path(root_dir) / child['name']
            child_exists = Path.exists(save_path)
            if child['mimeType'] == 'application/vnd.google-apps.folder':
                if not child_exists:
                    logger.info(f"Creating {save_path}.")
                    os.mkdir(save_path)
                    logger.info(f"{save_path} created.")
                self.download_from_gdrive(child['id'], str(Path(root_dir) / child['name']))
            else:
                if not child_exists:
                    logger.info(f"Downloading {save_path}.")
                    self.download_file(child['id'], save_path)
                    logger.info(f"{save_path} downloaded.")

    def folder_processor(self, folder_name: str, parent_folder: str) -> str:
        existent_folder = self.get_metadata(folder_name, parent_folder, type="folder")
        if not existent_folder:
            logger.info(f"{folder_name} doesn't exist. Attempting to create.")
            current_folder_id = self.upload_to_gdrive(
                folder_name, parents=[parent_folder], type="folder"
            )
            logger.info(f"{folder_name} folder created.")
        else:
            logger.info(f"{folder_name} folder exists.")
            current_folder_id = existent_folder[0]["id"]

        return current_folder_id

    def file_processor(self, path: str, file: str, current_folder_id) -> str:
        file_path = f"{path}/{file}"
        existent_file = self.get_metadata(file, current_folder_id)

        if not existent_file:
            file_id = self.upload_to_gdrive(file_path, parents=[current_folder_id])
        else:
            file_id = existent_file[0]["id"]
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
        saves_id = self.folder_ids[Path(DEFAULT_GDRIVE_REMOTE_SAVE_FOLDER).parts[-1]]
        game_id = self.folder_processor(game_name, saves_id)
        self.folder_ids[game_name] = game_id
        for path, dirs, files in os.walk(local_path):
            parts = Path(path).parts
            parent_folder_id = (
                self.folder_ids[path] if parts[-1] != top_folder else game_id
            )
            for folder_name in dirs:
                logger.info(f"Processing {path}\\{folder_name} folder.")
                folder_id = self.folder_processor(folder_name, parent_folder_id)
                self.folder_ids[f"{path}\\{folder_name}"] = folder_id
                logger.info(
                    f"Folder {path}\\{folder_name} processed. Folder id is: {folder_id}."
                )

            for file in files:
                logger.info(f"Processing {path}\\{file}.")
                file_id = self.file_processor(path, file, parent_folder_id)
                logger.info(f"{path}\\{file} processed. File id is: {file_id}.")


