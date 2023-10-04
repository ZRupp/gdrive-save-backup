import typing
from PyQt6 import QtCore
from PyQt6.QtCore import QModelIndex, QObject, Qt
import sys

sys.path[0] += "\\.."
from backend.file_discovery import *
from backend.utilities import *
import pathlib

COL_GAME_NAME = 0
COL_SAVE_LOCATION = 1

class SaveTableModel(QtCore.QAbstractTableModel):
    cellDataChanged = QtCore.pyqtSignal(int)
    def __init__(self, parent: QObject | None) -> None:
        super().__init__(parent)
        self.__raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self.__data = self.__format_data(self.__raw_data)
        self.__headers = ["Game Name", "Save Location"]

    def columnCount(self, parent: QModelIndex) -> int:
        return 2

    def rowCount(self, parent: QModelIndex) -> int:
        return len(self.__data)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> str:
        """
        Get data for a specific index and role.

        Args:
            index (QModelIndex): The model index to retrieve data for.
            role (Qt.ItemDataRole): The role for which to retrieve data.

        Returns:
            str: The data for the specified index and role.
        """

        row = index.row()
        column = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            return self.__data[row][column]

        if role == Qt.ItemDataRole.EditRole:
            return self.__data[row][column]

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ) -> str:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self.__headers[section]

    def __format_data(self, data: dict) -> list:
        """
        Format the raw data into a list for the model.

        Args:
            data (dict): The raw data dictionary.

        Returns:
            list: The formatted data as a list.
        """

        data = [[game_name, save_location] for game_name, save_location in data.items()]
        return data

    def update_saves(self):
        self.__raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self.__data = self.__format_data(self.__raw_data)

    def sort(self, column: int, order: Qt.SortOrder) -> None:
        if order == Qt.SortOrder.AscendingOrder:
            self.__data.sort(key=lambda x: x[column].lower())
        else:
            self.__data.sort(key=lambda x: x[column].lower(), reverse=True)
        self.layoutChanged.emit()

    def setData(self, index: QModelIndex, value: object, role: Qt.ItemDataRole) -> bool:
        """
        Set data for a specific index and role.

        Args:
            index (QModelIndex): The model index to set data for.
            value (object): The new value to set.
            role (Qt.ItemDataRole): The role for which to set data.

        Returns:
            bool: True if the data was successfully updated, False otherwise.
        """

        if not value.strip():
            return False

        if role == QtCore.Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()

            self.__update_underlying_data(index, value)
            self.__data[row][col] = (
                value if col == COL_GAME_NAME else str(pathlib.Path(value))
            )
            self.dataChanged.emit(index, index, [role])
            self.cellDataChanged.emit(col)
            return True
        return False

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return QtCore.Qt.ItemFlag.NoItemFlags
        col = index.column()
        if col == COL_GAME_NAME:
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled
                | QtCore.Qt.ItemFlag.ItemIsSelectable
                | QtCore.Qt.ItemFlag.ItemIsEditable
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
        else:
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
            )

    def __update_underlying_data(self, index: QModelIndex, new_data: str) -> bool:
        """
        Update the underlying data and save it to a JSON file.

        Returns:
            bool: True if the update was successful, False otherwise.

        TODO: make this work for deleting and adding new rows as well.
        """

        row = index.row()
        col = index.column()

        game_name = self.__data[row][COL_GAME_NAME]
        save_location = self.__data[row][COL_SAVE_LOCATION]

        if col == COL_GAME_NAME:
            del self.__raw_data[game_name]
            self.__raw_data[new_data] = save_location
        else:
            self.__raw_data[game_name] = str(pathlib.Path(new_data))

        save_to_json(self.__raw_data, DISCOVERED_FOLDERS_PATH)

        return True
    
    def add_row(self, game_name: str, save_location: str, index) -> bool:
        if game_name and save_location and not self.__raw_data.get(game_name):
            self.__raw_data[game_name] = save_location
            save_to_json(self.__raw_data, DISCOVERED_FOLDERS_PATH)
            self.__data.append([game_name, save_location])
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
            self.cellDataChanged.emit(COL_GAME_NAME)
            self.layoutChanged.emit()

            return True
        return False



    def delete_row(self, index: QModelIndex, role: Qt.ItemDataRole) -> bool:
        row = index.row()

        del self.__raw_data[self.__data[row][COL_GAME_NAME]]
        save_to_json(self.__raw_data, DISCOVERED_FOLDERS_PATH)
        del self.__data[row]

        self.dataChanged.emit(index, index, [role])
        self.layoutChanged.emit()