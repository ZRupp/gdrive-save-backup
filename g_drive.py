import os
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.fs import GDriveFileSystem

from datetime import datetime


class GDrive:
    """A Class allowing manipulation of the GoogleDrive object"""

    def __init__(self):
        self.__gauth = GoogleAuth()
        self.__gauth.LocalWebserverAuth()
        self.__drive = GoogleDrive(self.__gauth)
        self.__fs = GDriveFileSystem("root", google_auth=self.__gauth)

    def upload_to_g_drive(
        self,
        local_path: str,
        remote_path: str = "root/saves/",
    ) -> None:
        """Simple method to upload file to GDrive.

        TODO: Maybe handle uploading entire folders.
        TODO: Ask users if they want to preserve old saves if they would be deleted otherwise

        """

        if self.file_exists(remote_path):
            metadata = self.get_metadata(remote_path)
            local_modified_time = datetime.fromtimestamp(
                os.path.getmtime(local_path)
            ).isoformat()
            remote_modified_time = metadata["modifiedDate"]

            if local_modified_time > remote_modified_time:
                # This is probably not ideal since it is a destructive action.
                self.__fs.rm(remote_path, recursive=True)

                self.__fs.put(local_path, remote_path, recursive=True)

                print(f"Uploaded {local_path} to {remote_path}.")
            else:
                print(f"{remote_path} already exists and is up to date.")

        else:
            self.__fs.put(local_path, remote_path, recursive=True)
            print(f"Uploaded {local_path} to {remote_path}.")

    def file_exists(self, path: str) -> bool:
        """Simple method to check if the file exists remotely"""
        return self.__fs.exists(path)

    def get_metadata(self, path: str) -> dict:
        """Method to retrieve metada for a file in the user's GDrive."""

        title = path.split("/")[-1]
        q = {"q": f"title = '{title}' and trashed=False"}

        file_list = self.__drive.ListFile(q).GetList()

        return file_list[0]
