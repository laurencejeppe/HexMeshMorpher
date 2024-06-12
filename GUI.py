# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 19:29:14 2023

@author: ljr1e21
"""

import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (QIcon, QAction)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog,
                             QVBoxLayout, QComboBox, QPushButton, QHBoxLayout,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QGridLayout, QMessageBox, QLineEdit, QLabel)
import MeshObj
import amberg_mapping

class MeshMorpherGUI(QMainWindow):
    def __init__(self):
        super(MeshMorpherGUI,self).__init__()

        self.setWindowTitle("MeshMorphPy")

        self.WDIR = os.path.join(os.getcwd(), 'Meshes')
        if not os.path.exists(self.WDIR):
            os.makedirs(self.WDIR)

        self.initUI()

    def initUI(self):
        self.mainWidget = QWidget()
        self.files = {}
        self.filesDrop = list(self.files.keys())
        self.setCentralWidget(self.mainWidget)
        self.createActions()
        self.createMenus()

        self.layout = QVBoxLayout()

        self.file_manager = fileManager()
        self.layout.addWidget(self.file_manager)

        self.open_cdb_btn = QPushButton("Open CDB")

        self.layout.addWidget(self.open_cdb_btn)

        self.open_cdb_btn.clicked.connect(self.chooseOpenFile)

        self.hlayout = QHBoxLayout()
        self.hlayout.addStretch()

        # Element type selections
        self.element_type_CB = QComboBox()
        self.element_type_CB.addItems(['S4','S8R','C3D8', 'C3D4'])
        self.setStyleSheet("QComboBox {text-align: center;}")
        self.hlayout.addWidget(self.element_type_CB)

        self.hlayout.addStretch()

        # Unit converter
        self.convertUnits = QCheckBox()
        self.convertUnits.setText("Convert mm to m")
        self.hlayout.addWidget(self.convertUnits)
        self.hlayout.addStretch()

        self.layout.addLayout(self.hlayout)

        self.save_inp_btn = QPushButton("Save INP")

        self.layout.addWidget(self.save_inp_btn)

        self.save_inp_btn.clicked.connect(self.chooseSaveFile)

        self.mainWidget.setLayout(self.layout)
        self.resize(600,600)
        self.show()

    def createActions(self):
        self.openFile = QAction(QIcon('open.png'), 'Open', self,
                                shortcut='Ctrl+O',
                                triggered=self.chooseOpenFile)
        self.openQUADmesh = QAction(QIcon('open.png'), 'Open QUAD', self,
                                    triggered=self.load_quad_mesh)
        self.choose_wdir = QAction(QIcon('open.png'), 'Choose Working Directory',
                                  self, triggered=self.choose_WDIR)
        self.saveFile = QAction(QIcon('open.png'), 'Save', self,
                                shortcut='Ctrl+S',
                                triggered=self.chooseSaveFile)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               triggered=self.close)
        self.runAmberg = QAction(QIcon('open.png'), 'Run Amberg',
                                 self, triggered=self.run_amberg_mapping)
        self.openMorphOptions = QAction(QIcon("open.png"), 'Morph Options',
                                        self, triggered=self.open_morph_options)


    def createMenus(self):
        """
        Numpy style docstring.
        """
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openFile)
        self.fileMenu.addAction(self.openQUADmesh)
        self.fileMenu.addAction(self.choose_wdir)
        self.fileMenu.addAction(self.saveFile)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.amberg_nricp_menu = self.menuBar().addMenu("&Amberg")
        self.amberg_nricp_menu.addAction(self.runAmberg)
        self.morph_menu = self.menuBar().addMenu("&Morph Options")
        self.morph_menu.addAction(self.openMorphOptions)

    
    def open_morph_options(self):
        print('You have tried to open the morph options menu!')


    def chooseOpenFile(self):
        """
        Handles importing and reading of cdb

        """
        fname = QFileDialog.getOpenFileName(self,
                                            'Open file',
                                            directory=self.WDIR,
                                            filter="ANSYS (*.cdb)")

        if fname[0] == '':
            return
        self.cdb_file = fname[0]
        self.read_cdb()
    

    def chooseSaveFile(self):
        fname = QFileDialog.getSaveFileName(self,
                                            'Save file',
                                            directory=self.WDIR,
                                            filter="ABAQUS (*.inp)")

        if fname[0] == '':
            return
        self.inp_file = fname[0]
        #try:
        self.write_inp()
        #except AttributeError:
        #    print('A point has not been selected')

    def choose_WDIR(self):
        _dir = QFileDialog.getExistingDirectory(self,
                                                'Select Directory',
                                                directory=self.WDIR)
        self.WDIR = _dir

    def load_quad_mesh(self) -> MeshObj.STLMesh:
        """
        This is used to load a quad mesh created as either an stl or inp.
        If an inp is selected it will save it as an stl and load the stl.
        The loaded stl is then returned in a MeshObj STLMesh Object.
        If from_inp: the inp mesh is loaded converted to an stl file, saved
        and loaded.
        else: the stl file is loaded.
        """
        fname = QFileDialog.getOpenFileName(self,
                                            'Open file',
                                            directory=self.WDIR,
                                            filter="ABAQUS (*.inp), MESH (*.stl)")

        if fname[0] == '':
            return
        file_path = fname[0]
        file_folder_list = file_path[:-4].split('/')[:-1]
        file_folder_list[0] = file_folder_list[0] + '/'
        file_folder = os.path.join(*file_folder_list)
        file_name = file_path[:-4].split('/')[-1]

        if file_path[-4:] == '.inp':
            # Load liner surface inp file
            liner_surface_inp = MeshObj.LinerINPMesh(file_name, file_name,
                                                     file_folder)
            liner_surface_inp.rename(file_name, self.WDIR)
            liner_surface_inp.write_stl()   # Save as stl
            file_folder = self.WDIR
        elif file_path[-4:] != '.stl':
            return
        
        # Load surface stl file
        self.files[file_name] = MeshObj.STLMesh(file_name, file_name,
                                                file_folder)
        mesh_obj = self.files[file_name]
        self.file_manager.addRow(file_name, mesh_obj)
        self.filesDrop.append(file_name)

    def run_amberg_mapping(self):
        self.amberg_nricp = ambergOptions(self)
        self.amberg_nricp.show()


class ambergOptions(QMainWindow):
    def __init__(self, parent = None):
        super(ambergOptions, self).__init__(parent)
        self.setWindowTitle("Amberg Mapping")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.files = parent.files
        self.WDIR = parent.WDIR

        # Table to view loop options
        self.layout = QGridLayout()
        self.table = QTableWidget()
        self.table.setRowCount(4)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Stiffness', 'Landmarks', 'Rigid Transformation', 'Iterations'])
        self.table.setCurrentCell(1,3)
        self.table.setItem(1,2,1)
        self.n = self.table.rowCount()
        self.layout.addWidget(self.table, 0, 0)

        # Buttons to edit table
        self.table_edit_layout = QVBoxLayout()
        self.add_loop = QPushButton("Add Loop")
        self.table_edit_layout.addWidget(self.add_loop)
        self.del_loop = QPushButton("Delete Loop")
        self.table_edit_layout.addWidget(self.del_loop)
        self.edit_loop = QPushButton("Edit Loop")
        self.table_edit_layout.addWidget(self.edit_loop)
        self.layout.addLayout(self.table_edit_layout, 0, 1)

        # Options with checkboxes
        self.options_layout = QGridLayout()
        self.use_faces = QCheckBox()
        self.use_faces.setText("Use Faces")
        self.options_layout.addWidget(self.use_faces, 0, 0)
        self.use_landmarks = QCheckBox()
        self.use_landmarks.setText("Use Landmarks")
        self.options_layout.addWidget(self.use_landmarks, 0, 1)
        self.epsilon_text = QLabel("Epsilon")
        self.options_layout.addWidget(self.epsilon_text, 1, 0)
        self.epsilon_edit = QLineEdit()
        self.epsilon_edit.setPlaceholderText("0.001")
        self.options_layout.addWidget(self.epsilon_edit, 1, 1)
        self.gamma_text = QLabel("Gamma")
        self.options_layout.addWidget(self.gamma_text, 2, 0)
        self.gamma_edit = QLineEdit()
        self.gamma_edit.setPlaceholderText("1")
        self.options_layout.addWidget(self.gamma_edit, 2, 1)
        self.neighbors_text = QLabel("Neighbors")
        self.options_layout.addWidget(self.neighbors_text, 3, 0)
        self.neighbors_edit = QLineEdit()
        self.neighbors_edit.setPlaceholderText("8")
        self.options_layout.addWidget(self.neighbors_edit, 3, 1)
        self.distance_text = QLabel("Distance Threshold")
        self.options_layout.addWidget(self.distance_text, 4, 0)
        self.distance_edit = QLineEdit()
        self.distance_edit.setPlaceholderText("0.1")
        self.options_layout.addWidget(self.distance_edit, 4, 1)
        self.source_text = QLabel("Source Mesh")
        self.options_layout.addWidget(self.source_text, 5, 0)
        self.source = QComboBox()
        self.source.addItems(self.files)
        self.setStyleSheet("QComboBox {text-align: center;}")
        self.options_layout.addWidget(self.source, 5, 1)
        self.target_text = QLabel("Target Mesh")
        self.options_layout.addWidget(self.target_text, 6, 0)
        self.target = QComboBox()
        self.target.addItems(self.files)
        self.options_layout.addWidget(self.target, 6, 1)

        self.layout.addLayout(self.options_layout, 1, 0)

        self.run_amberg_btn = QPushButton("Run Amberg Mapping")
        self.run_amberg_btn.clicked.connect(self.initiate_amberg)
        self.layout.addWidget(self.run_amberg_btn, 2, 0)

        self.mainWidget.setLayout(self.layout)

        self.resize(520,400)

        # TODO: Add signals and controls for all of the above
        # TODO: Add mesh selection combobox

    def initiate_amberg(self):
        # TODO: Run checks to see if there are two different meshes selected for the morphing.
        # TODO: Get information from all the options
        source = self.files[self.source.currentText()]
        target = self.files[self.target.currentText()]
        output = MeshObj.STLMesh('Mapped Liner Surface Mesh',
                                 'MappedMesh',
                                 f_folder=self.WDIR,
                                 load=False)
        runs = self.table.rowCount()
        for row in range(runs):
            for i in range(4):
                print(self.table.item(row, i).text())

        # TODO: Call the amberg_mapping.py
        #amberg_mapping.AmbergMapping(source, target, output, steps, options)




class fileManager(QWidget):
    """
    Controls to manage the displayed 
    
    Example
    -------
    Perhaps an example implementation:

    >>> from GUIs.ampscanGUI import ampscanGUI

    """

    def __init__(self, parent = None):
        super(fileManager, self).__init__(parent)
        self.table = QTableWidget()
        self.layout = QGridLayout()
        self.layout.addWidget(self.table, 0, 0)
        self.setLayout(self.layout)
        self.table.setRowCount(0)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Name', 'Type', 'Colour', 'Opacity', 'Display'])
        self.n = self.table.rowCount()
        # Set the minimum table size to when it is fully expanded
        self.table.setMinimumWidth(self.table.frameWidth()*2
                                   + self.table.horizontalHeader().length()
                                   + self.table.verticalHeader().width())

    def addRow(self, name, amp):
        self.table.insertRow(self.n)
        self.table.setItem(self.n, 0, QTableWidgetItem(name))
        self.table.setItem(self.n, 1, QTableWidgetItem(amp.f_type))
        self.table.setItem(self.n, 2, QTableWidgetItem(str(amp.color)))
        self.table.setItem(self.n, 3, QTableWidgetItem(str(amp.opacity)))
        chkBoxItem = QTableWidgetItem()
        chkBoxItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        chkBoxItem.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        chkBoxItem.setCheckState(Qt.CheckState.Checked)

        self.table.setItem(self.n,4,chkBoxItem)
        self.n = self.table.rowCount()

    def getRow(self, i):
        row = []
        for r in range(self.table.columnCount() - 1):
            row.append(self.table.item(i, r).text())
        row.append(self.table.item(i, r+1).checkState())
        return row

    def setTable(self, name, color = [1.0, 1.0, 1.0], opacity=1.0, display=2):
        for i in range(self.n):
            if self.table.item(i, 0).text() == name:
                self.table.item(i, 2).setText(str(color))
                self.table.item(i, 3).setText(str(opacity))
                self.table.item(i, 4).setCheckState(display)

def show_message(message, message_type="err", title="An Error Occured..."):
    """
    Parameters
    ----------
    message : string
        The message to be displayed
    message_type : string
        The type of message e.g. "err" or "info"
    title : string
        The title of the dialog window

    Examples
    --------
    >>> show_message("test")
    >>> show_message("test2", "info", "test")

    """
    dialog = QMessageBox()
    dialog.setText(message)
    dialog.setWindowTitle(title)
    icons = {
        "err": QMessageBox.Critical,
        "info": QMessageBox.Information
    }
    dialog.setIcon(icons[message_type])
    dialog.setStandardButtons(QMessageBox.Ok)

    # Makes sure doesn't close until user closes it
    dialog.exec_()

    return dialog

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MeshMorpherGUI()
    win.show()
    sys.exit(app.exec())
