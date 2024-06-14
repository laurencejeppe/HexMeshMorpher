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
                             QGridLayout, QMessageBox, QLineEdit, QLabel,
                             QHeaderView)
import MeshObj
import amberg_mapping
import RBF_morpher

class MeshMorpherGUI(QMainWindow):
    def __init__(self):
        super(MeshMorpherGUI,self).__init__()

        self.setWindowTitle("MeshMorphPy")

        self.WDIR = os.path.join(os.getcwd(), 'Meshes')
        if not os.path.exists(self.WDIR):
            os.makedirs(self.WDIR)

        self.initUI()
        self.load_test_mesh("Offset mesh 3_m")
        self.load_test_mesh("Torso_noears_m")


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

        self.open_cdb_btn = QPushButton("Open QUAD Mesh")

        self.layout.addWidget(self.open_cdb_btn)

        self.open_cdb_btn.clicked.connect(self.load_quad_mesh)

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
        self.runRBF = QAction(QIcon("open.png"), 'Run RBF Morpher',
                              self, triggered=self.run_rbf_morpher)
        self.findLandmarks = QAction(QIcon("open.png"), 'Find Landmakrs',
                                     self, tirggered=self.find_landmarks)


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
        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.runAmberg)
        self.toolsMenu.addAction(self.runRBF)
        self.toolsMenu.addAction(self.findLandmarks)

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
        file_name = fname[0]

    def chooseSaveFile(self):
        fname = QFileDialog.getSaveFileName(self,
                                            'Save file',
                                            directory=self.WDIR,
                                            filter="ABAQUS (*.inp)")

        if fname[0] == '':
            return
        file_name = fname[0]

    def choose_WDIR(self):
        _dir = QFileDialog.getExistingDirectory(self,
                                                'Select Directory',
                                                directory=self.WDIR)
        self.WDIR = _dir
    
    def load_test_mesh(self, file_name):
        # Load surface stl file
        self.files[file_name] = MeshObj.STLMesh(file_name, file_name,
                                                self.WDIR)
        mesh_obj = self.files[file_name]
        self.file_manager.addRow(file_name, mesh_obj)
        self.filesDrop.append(file_name)


    def load_quad_mesh(self):
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
        self.amberg_nricp = Amberg_Mapping(self)
        self.amberg_nricp.show()


    def run_rbf_morpher(self):
        self.rbf_morpher = RBF_Morpher(self)
        self.rbf_morpher.show()

    def find_landmarks(self):
        pass

class Amberg_Mapping(QMainWindow):
    def __init__(self, parent = None):
        super(Amberg_Mapping, self).__init__(parent)
        self.setWindowTitle("Amberg Mapping")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.parent = parent
        self.files = parent.files
        self.WDIR = parent.WDIR

        # Table to view loop options
        self.layout = QGridLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Stiffness', 'Landmarks', 'Rigid Transformation', 'Iterations'])
        #self.table.setCurrentCell(1,3)
        self.set_step_table_defaults()
        self.table.horizontalHeader().setCascadingSectionResizes(True)
        self.set_step_table_sizing()
        self.layout.addWidget(self.table, 0, 0)

        # Buttons to edit table
        self.table_edit_layout = QVBoxLayout()
        self.add_loop_btn = QPushButton("Add Loop")
        self.add_loop_btn.clicked.connect(self.add_loop)
        self.table_edit_layout.addWidget(self.add_loop_btn)
        self.del_loop_btn = QPushButton("Delete Loop")
        self.del_loop_btn.clicked.connect(self.del_loop)
        self.table_edit_layout.addWidget(self.del_loop_btn)
        #self.edit_loop_btn = QPushButton("Edit Loop")
        #self.table_edit_layout.addWidget(self.edit_loop_btn)
        self.table_edit_layout.addStretch()
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
        self.epsilon_edit.setInputMask("9") # TODO: Adjust input masks
        self.epsilon_edit.setPlaceholderText("0.001")
        self.options_layout.addWidget(self.epsilon_edit, 1, 1)
        self.gamma_text = QLabel("Gamma")
        self.options_layout.addWidget(self.gamma_text, 2, 0)
        self.gamma_edit = QLineEdit()
        self.gamma_edit.setInputMask("9")
        self.gamma_edit.setPlaceholderText("1")
        self.options_layout.addWidget(self.gamma_edit, 2, 1)
        self.neighbors_text = QLabel("Neighbors")
        self.options_layout.addWidget(self.neighbors_text, 3, 0)
        self.neighbors_edit = QLineEdit()
        self.neighbors_edit.setInputMask("9")
        self.neighbors_edit.setPlaceholderText("8")
        self.options_layout.addWidget(self.neighbors_edit, 3, 1)
        self.distance_text = QLabel("Distance Threshold")
        self.options_layout.addWidget(self.distance_text, 4, 0)
        self.distance_edit = QLineEdit()
        self.distance_edit.setInputMask("9")
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

    def set_step_table_defaults(self) -> None:
        step_defaults = [
            [0.01, 0, 0.5, 10],
            [0.02, 2, 0.5, 10],
            [0.03, 5, 0.5, 10],
            [0.01, 8, 0.5, 10],
            [0.005, 10, 0.5, 10],
        ]
        self.table.setRowCount(len(step_defaults))
        for r, row in enumerate(step_defaults):
            for c, item in enumerate(row):
                self.table.setItem(r,c,QTableWidgetItem(str(item)))

    def set_step_table_sizing(self):
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def add_loop(self):
        default_row = [0.01, 0, 0.5, 10]
        if self.table.currentRow():
            row = self.table.currentRow()
        else:
            row = self.table.rowCount()
        self.table.insertRow(row)
        for i, item in enumerate(default_row):
            self.table.setItem(row, i, QTableWidgetItem(str(item)))

    def del_loop(self):
        if self.table.currentRow():
            self.table.removeRow(self.table.currentRow())
        else:
            show_message(message="Please select a row to be deleted first!",
                         title="Delete Loop Error")
    
    def initiate_amberg(self):
        if self.source.count() < 2:
            show_message(message="You need at least two meshes to perform an Amberg Mapping!",
                         title="Mesh Error")
            # For testing perposes add 
            self.target.setCurrentIndex(1)
            #return # TODO: Make this a return and delete above test file imports
        source = self.files[self.source.currentText()]
        target = self.files[self.target.currentText()]
        output = MeshObj.STLMesh('Mapped Liner Surface Mesh',
                                 'MappedMesh',
                                 f_folder=self.WDIR,
                                 load=False)
        rows = self.table.rowCount()
        steps = [[None for i in range(4)] for j in range(rows)]
        for row in range(rows):
            for col in range(4):
                steps[row][col] = float(self.table.item(row, col).text())
        e = float(self.epsilon_edit.text()) if self.epsilon_edit.hasAcceptableInput() else 0.001
        g = float(self.gamma_edit.text()) if self.gamma_edit.hasAcceptableInput() else 1
        n = int(self.neighbors_edit.text()) if self.neighbors_edit.hasAcceptableInput() else 8
        d = float(self.distance_edit.text()) if self.distance_edit.hasAcceptableInput() else 0.1
        f = self.use_faces.isChecked()
        l = self.use_landmarks.isChecked()

        options = {
            'gamma':g,
            'epsilon':e,
            'neighbors_count':n,
            'distance_threshold':d,
            'use_faces':f,
            'use_landmarks':l,
        }

        AM = amberg_mapping.AmbergMapping(sourcey=source, targety=target, mappedy=output, steps=steps, options=options)
        output_mesh = AM.mapped
        self.parent.files[output_mesh.f_name] = output_mesh
        self.parent.file_manager.addRow(output_mesh.f_name, output_mesh)
        self.parent.filesDrop.append(output_mesh.f_name)
        self.close()

class RBF_Morpher(QMainWindow):
    def __init__(self, parent = None):
        super(RBF_Morpher, self).__init__(parent)
        self.setWindowTitle("RBF Morphing")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.parent = parent

        self.main_layout = QVBoxLayout()

        # Selected file that has is unmapped
        self.unmapped_text = QLabel("Unmapped Mesh")
        self.main_layout.addWidget(self.unmapped_text)
        self.unmapped = QComboBox()
        self.unmapped.addItems(self.parent.files)
        self.setStyleSheet("QComboBox {text-align: center;}")
        self.main_layout.addWidget(self.unmapped)
        # Selected file that has been mapped to surfaces
        self.mapped_text = QLabel("Mapped Mesh")
        self.main_layout.addWidget(self.mapped_text)
        self.mapped = QComboBox()
        self.mapped.addItems(self.parent.files)
        self.main_layout.addWidget(self.mapped)
        self.mapped.setCurrentIndex(1)
        # Selected file to be morphed
        self.morphee_text = QLabel("Morph This")
        self.main_layout.addWidget(self.morphee_text)
        self.morphee = QComboBox()
        self.morphee.addItems(self.parent.files)
        self.main_layout.addWidget(self.morphee)
        self.morphee.setCurrentIndex(2)
        

        self.run_morph_btn = QPushButton("Run Amberg Mapping")
        self.run_morph_btn.clicked.connect(self.initiate_morph)
        self.main_layout.addWidget(self.run_morph_btn)

        self.mainWidget.setLayout(self.main_layout)

        self.resize(520,400)

    def initiate_morph(self):
        unmapped = self.files[self.unmapped.currentText()]
        mapped = self.files[self.mapped.currentText()]
        mrophee = self.files[self.morphee.currentText()]

        #morpher = RBF_morpher.RBFMorpher()
        print('Inititiated Morphing')


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
    dialog.exec()

    return dialog

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MeshMorpherGUI()
    win.show()
    sys.exit(app.exec())
