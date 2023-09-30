from SaveTableModel import SaveTableModel
import sys
sys.path[0] += '\\..'
from backend.file_discovery import start_discovery
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtGui import QCursor

qt_creator_file = "./frontend/application.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.model = SaveTableModel(None)
        self.savesTableView.setModel(self.model)
        self.update_view()
        self.discover_button.clicked.connect(self.discover)
        self.savesTableView.doubleClicked.connect(self.openFileDialog)

    def __busy_cursor_decorator(func):
        def wrapper(self):
            """Wrapper to change cursor to busy cursor when process is running."""
            self.setCursor(QCursor(Qt.CursorShape.BusyCursor))
            func(self)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        return wrapper  


    @__busy_cursor_decorator
    def discover(self):
        """Method to link backend folder discovery method with frontend."""
        start_discovery()
        self.model.update_saves()
        self.model.layoutChanged.emit()
        self.update_view()
        

    def update_view(self):
        self.savesTableView.resizeColumnsToContents()
        self.savesTableView.resizeRowsToContents()

    def openFileDialog(self, index: QModelIndex) -> bool:
        if index.column() == 1:

            file_dialog = QtWidgets.QFileDialog(self)
            file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
            file_dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.List)

            # Set the directory to the one saved.
            role = Qt.ItemDataRole.EditRole
            path = self.model.data(index, role)
            file_dialog.setDirectory(path)

            selected_path = file_dialog.getExistingDirectory(self, "Select Directory")

            if selected_path:
                # Perform actions with the selected path (e.g., update model or display path)
                print("Selected Path:", selected_path)

if __name__ =='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()