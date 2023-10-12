from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import QModelIndex, QObject, Qt
import sys

sys.path[0] += "\\.."
from backend.file_discovery import *
from backend.utilities import *
from backend.GDrive import GDrive
import pathlib


COL_GAME_NAME = 0
COL_SAVE_LOCATION = 1


class SaveTableModel(QtCore.QAbstractTableModel):
    cellDataChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent: QObject | None) -> None:
        super().__init__(parent)
        self._raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self._data = self.__format_data(self._raw_data)
        self._headers = ["Game Name", "Save Location"]
        self._checkboxes = [True] * len(self._data)
        self._g_drive = GDrive()

    def columnCount(self, parent: QModelIndex) -> int:
        return len(self._headers)

    def rowCount(self, parent: QModelIndex) -> int:
        return len(self._data)

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

        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return self._data[row][column]

        if role == Qt.ItemDataRole.CheckStateRole:
            if column == 0:
                return (
                    Qt.CheckState.Checked
                    if self._checkboxes[row]
                    else Qt.CheckState.Unchecked
                )

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
        row = index.row()
        col = index.column()

        if role == QtCore.Qt.ItemDataRole.EditRole:
            if not value.strip():
                return False
            self._update_underlying_data(index, value)
            self._data[row][col] = (
                value if col == COL_GAME_NAME else str(pathlib.Path(value))
            )
            self.dataChanged.emit(index, index, [role])
            self.cellDataChanged.emit(col)
            return True

        if role == Qt.ItemDataRole.CheckStateRole:
            self._checkboxes[row] = value
            self.dataChanged.emit(index, index, [role])
        return False

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole
    ) -> str:
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return self._headers[section]
        
        if (
            orientation == Qt.Orientation.Vertical
            and role == Qt.ItemDataRole.DisplayRole
        ):
            return section

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
        self._raw_data = load_from_json(DISCOVERED_FOLDERS_PATH)
        self._data = self.__format_data(self._raw_data)
        self._checkboxes = [False] * len(self._data)

    def sort(self, column: int, order: Qt.SortOrder) -> None:
        if order == Qt.SortOrder.AscendingOrder:
            self._data.sort(key=lambda x: x[column].lower())
        else:
            self._data.sort(key=lambda x: x[column].lower(), reverse=True)
        self.layoutChanged.emit()

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

    def add_row(self, game_name: str, save_location: str, index) -> bool:
        if game_name and save_location and not self._raw_data.get(game_name):
            self._raw_data[game_name] = save_location
            save_to_json(self._raw_data, DISCOVERED_FOLDERS_PATH)
            self._data.append([game_name, save_location])
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
            self.cellDataChanged.emit(COL_GAME_NAME)
            self.layoutChanged.emit()

            return True
        return False

    def delete_row(self, index: QModelIndex, role: Qt.ItemDataRole) -> bool:
        row = index.row()

        del self._raw_data[self._data[row][COL_GAME_NAME]]
        save_to_json(self._raw_data, DISCOVERED_FOLDERS_PATH)
        del self._data[row]

        self.dataChanged.emit(index, index, [role])
        self.layoutChanged.emit()

    def begin_upload(self, data_to_upload: list):

        for game_name, location in data_to_upload:
            print(game_name, location)
            self._g_drive.upload_to_gdrive(location, game_name)


    def select_all(self, isChecked: bool) -> bool:
        self._checkboxes = [isChecked] * len(self._data)
        self.layoutChanged.emit()


    def retrieve_selected_data(self):
        return [row for (row, checked) in zip(self._data, self._checkboxes) if checked]

    def _update_underlying_data(self, index: QModelIndex, new_data: str) -> bool:
        """
        Update the underlying data and save it to a JSON file.

        Returns:
            bool: True if the update was successful, False otherwise.

        TODO: make this work for deleting and adding new rows as well.
        """

        row = index.row()
        col = index.column()

        game_name = self._data[row][COL_GAME_NAME]
        save_location = self._data[row][COL_SAVE_LOCATION]

        if col == COL_GAME_NAME:
            del self._raw_data[game_name]
            self._raw_data[new_data] = save_location
        else:
            self._raw_data[game_name] = str(pathlib.Path(new_data))

        save_to_json(self._raw_data, DISCOVERED_FOLDERS_PATH)

        return True