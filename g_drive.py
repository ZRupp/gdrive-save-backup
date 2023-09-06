from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class GDrive:
    '''A Class allowing manipulation of the GoogleDrive object'''
    def __init__(self):
        self.gauth = GoogleAuth()
        self.gauth.LocalWebserverAuth()
        self.drive = GoogleDrive(self.gauth)

    
    def get_file_list(self, query) -> list:
        '''Returns a list of folders and/or files matching the query string'''

        return self.drive.ListFile({'q': "title = 'saves' and trashed=false and mimeType = 'application/vnd.google-apps.folder'"}).GetList()


if __name__ == '__main__':
    

    g_drive = GDrive()

    query = {'q': "name contains 'saves' and trashed=false"}

    file_list = g_drive.get_file_list(query)

    for f in file_list:
        print(f)

    