from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.fs import GDriveFileSystem

class GDrive:
    '''A Class allowing manipulation of the GoogleDrive object'''
    def __init__(self):
        self.__gauth = GoogleAuth()
        self.__gauth.LocalWebserverAuth()
        self.__drive = GoogleDrive(self.__gauth)
        self.__fs = GDriveFileSystem(
            "root",
            google_auth=self.__gauth
        )

    
    def get_file_list(self, query) -> list:
        '''Returns a list of folders and/or files matching the query string'''

        return self.__drive.ListFile(query).GetList()
    
    def upload_to_g_drive(self, local_path: str, remote_path: str = 'root/saves/') -> None:
        ''' Simple method to upload file to GDrive.
        '''

        self.__fs.put(local_path, remote_path, recursive=True)

    def file_exists(self, path: str) -> bool:
        '''Simple method to check if the file exists remotely'''
        return self.__fs.exists(path)

