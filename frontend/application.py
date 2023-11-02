import typing
from SaveTableModel import SaveTableModel
import sys
sys.path[0] += '\\..'
import pathlib
from backend.file_discovery import start_discovery
from PyQt6 import QtCore, QtGui, QtWidgets, uic
from PyQt6.QtCore import Qt, QModelIndex, QThread
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QMessageBox, QHeaderView, QProgressDialog
import time

qt_creator_file = "./frontend/application.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        header=CheckBoxHeader(parent=self.savesTableView)
        self.model = SaveTableModel(None)
        self.savesTableView.setModel(self.model)
        header.clicked.connect(self.model.select_all)
        self.savesTableView.setHorizontalHeader(header)
        self.savesTableView.horizontalHeader().setSortIndicator(0, Qt.SortOrder.AscendingOrder)
        
        self.update_view()
        self.discover_button.clicked.connect(self.discover)
        self.savesTableView.doubleClicked.connect(self.editFilePath)
        self.model.cellDataChanged.connect(self.sort_by_column)
        self.remove_button.clicked.connect(self.remove_row)
        self.add_button.clicked.connect(self.add_row)
        self.upload_button.clicked.connect(self.upload_data)

        del_key = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Delete, self.savesTableView)
        del_key.activated.connect(self.remove_row)

        self.confirmation_box = QMessageBox()
        self.confirmation_box.setWindowTitle('Are you sure?')
        self.confirmation_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No);
        self.confirmation_box.setDefaultButton(QMessageBox.StandardButton.No)



    def __busy_cursor_decorator(func):
        def wrapper(self):
            """Wrapper to change cursor to busy cursor when process is running."""
            self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
            func(self)
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        return wrapper  


    @__busy_cursor_decorator
    def discover(self):
        """Method to link backend folder discovery method with frontend."""
        start_discovery()
        self.model.update_saves()
        self.model.layoutChanged.emit()
        self.sort_by_column(0)
        self.update_view()
        

    def update_view(self):
        self.savesTableView.resizeColumnsToContents()
        self.savesTableView.resizeRowsToContents()

    def openFileDialog(self) -> str:
        file_dialog = QtWidgets.QFileDialog(self)
        file_dialog.setFileMode(QtWidgets.QFileDialog.FileMode.Directory)
        file_dialog.setViewMode(QtWidgets.QFileDialog.ViewMode.List)

        return file_dialog

    def editFilePath(self, index: QModelIndex) -> bool:
        if index.column() == 1:

            file_dialog = self.openFileDialog()

            # Set the directory to the one saved.
            role = Qt.ItemDataRole.EditRole
            path = self.model.data(index, role)
            file_dialog.setDirectory(path)

            selected_path = file_dialog.getExistingDirectory(self, "Select Directory")

            if selected_path:
                self.model.setData(index, selected_path, role)
                self.update_view()

    def sort_by_column(self, column: int, sortOrder: Qt.SortOrder = None) -> None:
        if not sortOrder:
            header = self.savesTableView.horizontalHeader()
            sortOrder = header.sortIndicatorOrder()
        self.model.sort(column, sortOrder)

    def upload_data(self):
        message = 'Do you really want to upload saves for the following games?\n\n'
        
        save_list = self.model.retrieve_selected_data()

        for game_name, _ in save_list:
            message += f'{game_name}\n'

        
        self.confirmation_box.setText(message)
        confirmation_choice = self.confirmation_box.exec()

        if confirmation_choice == QMessageBox.StandardButton.Yes:
            self.progress = self.create_progress_dialog()
            self.upload_thread = self.create_upload_thread(save_list)
            self.upload_thread.start()

    def create_upload_thread(self, save_list: list):
        upload_thread = UploadHelper(self.model.begin_upload)
        upload_thread.started.connect(self.handle_thread_start)
        upload_thread.update_signal.connect(self.update_dialog)
        upload_thread.finished.connect(self.handle_thread_finish)
        upload_thread.set_save_list(save_list)    

        return upload_thread

    def create_progress_dialog(self):
        progress = CleanupProcessingProgressDialog()
        progress.hide()
        progress.userCancel.connect(self.cancel_dialog)

        return progress

    def update_dialog(self, value: int, label: str):
        self.progress.setLabelText(f"Uploading {label}...")
        self.progress.setValue(value)

    def cancel_dialog(self):
        if self.upload_thread.isRunning():
            label_text = self.progress.labelText()
            self.progress.setLabelText(f"Finishing {label_text[0].lower() + label_text[1:]}. Please wait.")
            self.progress.setCancelButtonText("Please Wait.")
            self.progress.setDisabled(True)
            self.upload_thread.handle_cancelation()
            self.upload_thread.quit()
            

    def handle_thread_start(self):
        num_files = len(self.upload_thread.save_list)
        self.progress.setMinimum(0)
        self.progress.setMaximum(num_files)
        self.progress.setWindowTitle('Uploading Saves')
        self.progress.setMinimumDuration(0)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.setValue(0)
        self.progress.setLabelText("Uploading saves...")
        self.progress.show()
        
    def handle_thread_finish(self):
        self.progress.close()

    def remove_row(self):
        index = self.savesTableView.currentIndex()
        
        if index.row() == -1:
            index = self.model.index(self.model.rowCount(index) - 1, 0)    
        if index.column() != 0:
            index = index.siblingAtColumn(0)

        game_name = index.data(Qt.ItemDataRole.EditRole)

        self.confirmation_box.setText(f"Are you sure you want stop tracking saves for {game_name}?")
        confirmation_choice = self.confirmation_box.exec()
        if confirmation_choice == QMessageBox.StandardButton.Yes:
            role = Qt.ItemDataRole.EditRole
            self.model.delete_row(index, role)

    def add_row(self):
        file_dialog = self.openFileDialog()
        path = pathlib.Path(file_dialog.getExistingDirectory(self, "Select Directory"))
        input_message = QtWidgets.QInputDialog()
        game_name = input_message.getText(self, 'Game Name', 'Choose Game Name')
        index = self.savesTableView.currentIndex()
        if game_name[1]:
        
            self.model.add_row(game_name[0], str(path), index)

class CleanupProcessingProgressDialog(QProgressDialog):
    userCancel = QtCore.pyqtSignal()
    
    def __init__(self):
        super().__init__()
        cancelButton = self.findChild(QtWidgets.QPushButton)
        cancelButton.clicked.disconnect(self.canceled)
        cancelButton.clicked.connect(self.userCancel)

        

    def reject(self):
        pass

    def closeEvent(self, event) -> None:
        if event.spontaneous:
            event.ignore()

class UploadHelper(QThread):
    update_signal = QtCore.pyqtSignal(int, str)

    def __init__(self, upload_function, save_list: list = None):
        super().__init__()
        self.upload_function = upload_function
        self.save_list = save_list
        self.canceled = False
        
    def handle_cancelation(self):
        self.canceled = True

    def run(self):
        for i, (game_name, location) in enumerate(self.save_list):
            if self.canceled:
                break
            self.update_signal.emit(i, game_name)
            self.upload_function(game_name, location)
        self.update_signal.emit(len(self.save_list), 'Finished!')
        self.canceled = False
        
    def set_save_list(self, save_list: list):
        self.save_list = save_list

class CheckBoxHeader(QHeaderView):
    ''' Class to add a header checkbox to the first column of horizontal header.
        Modified from https://stackoverflow.com/questions/30932528/adding-checkbox-as-vertical-header-in-qtableview/30934160#30934160
        Courtesy https://stackoverflow.com/users/4720935/mel
    '''
    clicked=QtCore.pyqtSignal(bool)

    def __init__(self,orientation=Qt.Orientation.Horizontal,parent=None):
        super(CheckBoxHeader,self).__init__(orientation,parent)
        self.isChecked=True

    def paintSection(self,painter,rect,logicalIndex):
        painter.save()
        super(CheckBoxHeader,self).paintSection(painter,rect,logicalIndex)
        painter.restore()
        if logicalIndex==0:
            option=QtWidgets.QStyleOptionButton()
            option.rect= QtCore.QRect(3,1,20,20)  #may have to be adapt
            option.state= QtWidgets.QStyle.StateFlag.State_Enabled | QtWidgets.QStyle.StateFlag.State_Active
            if self.isChecked:
                option.state|=QtWidgets.QStyle.StateFlag.State_On
            else:
                option.state|=QtWidgets.QStyle.StateFlag.State_Off
            self.style().drawControl(QtWidgets.QStyle.ControlElement.CE_CheckBox,option,painter)

    def mousePressEvent(self,event):
        if self.isChecked:
            self.isChecked=False
        else:
            self.isChecked=True
        self.clicked.emit(self.isChecked)
        self.viewport().update()


if __name__ =='__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()