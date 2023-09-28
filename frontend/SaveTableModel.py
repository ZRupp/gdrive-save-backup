from PyQt6 import QtCore
from PyQt6.QtCore import QModelIndex, QObject, Qt
import sys
sys.path[0] += '\\..'
from backend.file_discovery import *
from backend.utilities import *

class SaveTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent: QObject | None) -> None:
        super().__init__(parent)
        self.__raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self.__data = self.__format_data(self.__raw_data)
        
        

    def columnCount(self, parent: QModelIndex) -> int:
        return 2
    
    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.__data)
    
    def data(self, index: QModelIndex, role: int):
        if role == Qt.ItemDataRole.DisplayRole:
            row = index.row()
            column = index.column()
            return self.__data[row][column]

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            print(section)
            return ["Game Name", "Save Location"][section]

    def __format_data(self, data: dict) -> list:
        data = [[game_name, save_location] for game_name, save_location in data.items()]
        data.sort()
        return data

    def update_saves(self):
        print('hello')
        self.__raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self.__data = self.__format_data(self.__raw_data)
        
        