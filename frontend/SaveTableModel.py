import typing
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
    
    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> str:
        
        row = index.row()
        column = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            return self.__data[row][column]
        
        if role == Qt.ItemDataRole.EditRole:
            return self.__data[row][column]    

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole) -> str:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            
            return ["Game Name", "Save Location"][section]

    def __format_data(self, data: dict) -> list:
        data = [[game_name, save_location] for game_name, save_location in data.items()]
        data.sort()
        return data

    def update_saves(self):
        print('hello')
        self.__raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self.__data = self.__format_data(self.__raw_data)

    def sort(self, column: int, order: Qt.SortOrder) -> None:
        print(order, column)
        if order == Qt.SortOrder.AscendingOrder:
            self.__data.sort(key = lambda x: x[column].lower())
        else:
            self.__data.sort(key = lambda x: x[column].lower(), reverse=True)
        self.layoutChanged.emit()

    def setData(self, index: QModelIndex, value: object, role: Qt.ItemDataRole) -> bool:
        print('hello')
        if role == QtCore.Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()

            self.__update_underlying_data(self.__data[row][:], value)
            print(self.__raw_data)
            self.__data[row][col] = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        col = index.column()
        if col == 0:
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEditable
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        
    def __update_underlying_data(self, old_data: list, new_data: str) -> bool:
        game_name = old_data[0]
        save_location = old_data[1]

        del self.__raw_data[game_name]
        self.__raw_data[new_data] = save_location

        return True

