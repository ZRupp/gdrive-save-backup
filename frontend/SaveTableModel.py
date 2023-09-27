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
        self.saves = load_from_json(DISCOVERED_FOLDERS_PATH)

    def columnCount(self, index) -> int:
        return 2
    
    def rowCount(self, index) -> int:
        return len(self.saves)
    
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int):
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return ["X", "Y", "Z"][section]