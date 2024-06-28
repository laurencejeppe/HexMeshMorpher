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
                             QHeaderView, QDoubleSpinBox, QSpinBox,
                             QAbstractSpinBox, QStyle, QDialog)
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

        self.layout = QHBoxLayout()

        self.file_manager = fileManager()
        self.layout.addWidget(self.file_manager)

        self.options_layout = QVBoxLayout()
        self.open_tri_btn = QPushButton("Open TRI Mesh")
        self.open_tri_btn.clicked.connect(self.load_mesh_dialog)
        self.options_layout.addWidget(self.open_tri_btn)
        self.open_inp_btn = QPushButton("Open INP Mesh")
        self.open_inp_btn.clicked.connect(self.load_inp_mesh)
        self.options_layout.addWidget(self.open_inp_btn)
        self.change_mesh_units_btn = QPushButton("Change Selected Mesh Units")
        self.change_mesh_units_btn.clicked.connect(self.change_mesh_units)
        self.options_layout.addWidget(self.change_mesh_units_btn)
        
        self.options_layout.addStretch()
        self.layout.addLayout(self.options_layout)

        self.mainWidget.setLayout(self.layout)
        #self.resize(600,600)
        self.setFixedSize(self.size())
        self.show()

    def createActions(self):
        self.openFile = QAction(QIcon('open.png'), 'Open', self,
                                shortcut='Ctrl+O',
                                triggered=self.chooseOpenFile)
        self.openTRImesh = QAction(QIcon('open.png'), 'Open TRI', self,
                                    triggered=self.load_tri_mesh)
        self.openINPmesh = QAction(QIcon("open.png"), 'Open INP', self,
                                   triggered=self.load_inp_mesh)
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
                                     self, triggered=self.find_landmarks)


    def createMenus(self):
        """
        Numpy style docstring.
        """
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.openFile)
        self.fileMenu.addAction(self.openTRImesh)
        self.fileMenu.addAction(self.openINPmesh)
        self.fileMenu.addAction(self.choose_wdir)
        self.fileMenu.addAction(self.saveFile)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        self.toolsMenu = self.menuBar().addMenu("&Tools")
        self.toolsMenu.addAction(self.runAmberg)
        self.toolsMenu.addAction(self.runRBF)
        self.toolsMenu.addAction(self.findLandmarks)

    def chooseOpenFile(self, type_filter: str, prompt:str='Open File'):
        """ Handles importing and reading of new files """
        fname = QFileDialog.getOpenFileName(self,
                                            prompt,
                                            directory=self.WDIR,
                                            filter=type_filter)

        if fname[0] == '':
            return None
        return fname[0]

    def chooseSaveFile(self):
        fname = QFileDialog.getSaveFileName(self,
                                            'Save file',
                                            directory=self.WDIR,
                                            filter="ABAQUS (*.inp)")

        if fname[0] == '':
            show_message("Error loading mesh!")
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

    
    def load_mesh_dialog(self, stl=True, inp=True):
        stl_string = "MESH (*.stl)"
        inp_string = "ABAQUS (*.inp)"
        if not stl:
            typestring = inp_string
        elif not inp:
            typestring = stl_string
        else:
            typstring = inp_string + ', ' + stl_string
        
        fname = self.chooseOpenFile(typestring)
        
        if not fname:
            show_message("Mesh selection has failed")
            return
        
        file_path = fname
        file_folder_list = file_path[:-4].split('/')[:-1]
        file_folder_list[0] = file_folder_list[0] + '/'
        file_folder = os.path.join(*file_folder_list)
        file_name = file_path[:-4].split('/')[-1]

        if file_path[-4:] == '.inp':
            # Load inp mesh
            mesh = MeshObj.INPMesh(file_name, file_name, file_folder)
            #inp_mesh.rename(file_name, self.WDIR)
            #inp_mesh.write_stl()   # Save as stl
            #file_folder = self.WDIR
        elif file_path[-4:] == '.stl':
            mesh = MeshObj.STLMesh(file_name, file_name, file_folder)
        else:
            show_message("Mesh selection has failed")
            return


        # TODO: Need to finish off this function which will replace the following two seperate functions
        # Add options to decide if you want to convert the mesh or change the units or just load it as is
        d = QDialog()
        main_layout = QHBoxLayout()




        b1 = QPushButton("")
        d.setWindowTitle("Load Mesh")
        d.setWindowModality(Qt.WindowModality.ApplicationModal)
        d.exec()

        self.files[file_name] = MeshObj.STLMesh(file_name, file_name,
                                                file_folder)
        mesh_obj = self.files[file_name]
        self.file_manager.addRow(file_name, mesh_obj)
        self.filesDrop.append(file_name)


    def load_tri_mesh(self):
        """
        This is used to load a tri mesh created as either an stl or inp.
        If an inp is selected it will save it as an stl and load the stl.
        The loaded stl is then returned in a MeshObj STLMesh Object.
        If from_inp: the inp mesh is loaded converted to an stl file, saved
        and loaded.
        else: the stl file is loaded.
        """
        fname = self.chooseOpenFile("ABAQUS (*.inp), MESH (*.stl)")
        if not fname:
            return
        file_path = fname
        file_folder_list = file_path[:-4].split('/')[:-1]
        file_folder_list[0] = file_folder_list[0] + '/'
        file_folder = os.path.join(*file_folder_list)
        file_name = file_path[:-4].split('/')[-1]

        if file_path[-4:] == '.inp':
            # Load liner surface inp file
            liner_surface_inp = MeshObj.INPMesh(file_name, file_name,
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

    def load_inp_mesh(self):
        fname = self.chooseOpenFile("ABAQUS (*.inp)")
        if not fname:
            return
        file_path = fname
        file_folder_list = file_path[:-4].split('/')[:-1]
        file_folder_list[0] = file_folder_list[0] + '/'
        file_folder = os.path.join(*file_folder_list)
        file_name = file_path[:-4].split('/')[-1]

        if file_path[-4:] == '.inp':
            # Load liner surface inp file
            inp = MeshObj.INPMesh(file_name, file_name, file_folder)
            inp.rename(file_name, self.WDIR)
            file_folder = self.WDIR
        else:
            return
        
        # Load surface stl file
        self.files[file_name] = inp
        self.file_manager.addRow(file_name, inp)
        self.filesDrop.append(file_name)

    def change_mesh_units(self):
        if not self.file_manager.table.selectedItems():
            show_message(message="Please select a mesh in the table to change the units first!",
                         title="Item Selection Error")
        rows = []
        for item in self.file_manager.table.selectedItems():
            rows.append(self.file_manager.table.row(item))
        rows = set(rows)
        for row in rows:
            row = self.file_manager.table.currentRow()
            item = self.file_manager.table.item(row, 0).text()
            units = self.file_manager.table.item(row, 3).text()
            units = "mm" if units == "m" else "m"
            factor = 1000 if units == "m" else 0.001
            self.files[item].change_units(factor, units)
            self.file_manager.table.item(row, 3).setText(units)
        
    def run_amberg_mapping(self):
        self.amberg_nricp = Amberg_Mapping(self)
        self.amberg_nricp.show()

    def run_rbf_morpher(self):
        self.rbf_morpher = RBF_Morpher(self)
        self.rbf_morpher.show()

    def find_landmarks(self):
        self.landmark_finder = landmarkFinder(self)
        self.landmark_finder.show()


class Open_Mesh_Dialog(QDialog):
    def __init__(self, parent = None):
        super(Open_Mesh_Dialog, self).__init__(parent)
        # TODO: Fill this in to have a dialog for loading files
        # to give options how you load the file and what file you
        # are loading.

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
        self.table.setHorizontalHeaderLabels(['Stiffness',
                                              'Landmarks',
                                              'Rigid Transformation',
                                              'Iterations'])
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
        self.epsilon_edit = QDoubleSpinBox()
        self.epsilon_edit.setDecimals(5)
        self.epsilon_edit.setRange(0.00001, 0.1)
        self.epsilon_edit.setValue(0.001)
        self.epsilon_edit.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        self.options_layout.addWidget(self.epsilon_edit, 1, 1)
        self.gamma_text = QLabel("Gamma")
        self.options_layout.addWidget(self.gamma_text, 2, 0)
        self.gamma_edit = QSpinBox()
        self.gamma_edit.setRange(1, 100)
        self.gamma_edit.setValue(1)
        self.options_layout.addWidget(self.gamma_edit, 2, 1)
        self.neighbors_text = QLabel("Neighbors")
        self.options_layout.addWidget(self.neighbors_text, 3, 0)
        self.neighbors_edit = QSpinBox()
        self.neighbors_edit.setRange(1, 99)
        self.neighbors_edit.setValue(8)
        self.options_layout.addWidget(self.neighbors_edit, 3, 1)
        self.distance_text = QLabel("Distance Threshold")
        self.options_layout.addWidget(self.distance_text, 4, 0)
        self.distance_edit = QDoubleSpinBox()
        self.distance_edit.setDecimals(2)
        self.distance_edit.setRange(0.01, 1)
        self.distance_edit.setValue(0.1)
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

        self.resize(530,450)

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
        e = float(self.epsilon_edit.value()) if self.epsilon_edit.hasAcceptableInput() else 0.001
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
        # Selected file to be morphed
        self.morphee_text = QLabel("Morph This")
        self.main_layout.addWidget(self.morphee_text)
        self.morphee = QComboBox()
        self.morphee.addItems(self.parent.files)
        self.main_layout.addWidget(self.morphee)
        

        self.run_morph_btn = QPushButton("Run Amberg Mapping")
        self.run_morph_btn.clicked.connect(self.initiate_morph)
        self.main_layout.addWidget(self.run_morph_btn)

        self.mainWidget.setLayout(self.main_layout)

        self.resize(520,400)

    def initiate_morph(self):
        if self.source.count() < 3:
            show_message(message="You need at least two meshes to perform an Amberg Mapping!",
                         title="Mesh Error")
            # For testing perposes add
            self.unmapped.setCurrentIndex(0)
            self.mapped.setCurrentIndex(1)
            self.morphee.setCurrentIndex(2)
            # return # TODO: Make this a return and delete above test file imports
        unmapped = self.files[self.unmapped.currentText()]
        mapped = self.files[self.mapped.currentText()]
        morphee = self.files[self.morphee.currentText()]

        morpher = RBF_morpher.RBFMorpher(unmapped, mapped, RBF_Morpher.custom_RBF)

        # Morph the liner nodes and replace them in the liner mesh objected
        morphee.nodes[:,1:] = morpher.morph_vertices(morphee.nodes[:,1:])
        name = morphee.f_name + "_mrophed.inp"
        morphee.write_inp(name)
        self.close()

class landmarkFinder(QMainWindow):
    def __init__(self, parent = None):
        super(landmarkFinder, self).__init__(parent)
        self.setWindowTitle("Landmark Finder")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.parent = parent


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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Name', 'Type', 'Description', 'Units'])
        self.n = self.table.rowCount()
        #self.table.verticalHeader().hide()
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.table.horizontalHeader().setSectionsClickable(False)
        self.table.setCornerButtonEnabled(False)
        # Set the minimum table size to when it is fully expanded
        #self.table.setMinimumWidth(self.table.frameWidth()*2
        #                           + self.table.horizontalHeader().length()
        #                           + self.table.verticalHeader().width())
        #self.table.setMaximumWidth(self.table.frameWidth()*2
        #                           + self.table.horizontalHeader().length()
        #                           + self.table.verticalHeader().width())

    def addRow(self, name, amp):
        self.table.insertRow(self.n)
        name_item = QTableWidgetItem(name)
        self.table.setItem(self.n, 0, name_item)
        f_type_item = QTableWidgetItem(amp.f_type)
        f_type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(self.n, 1, f_type_item)
        description_item = QTableWidgetItem(amp.description)
        self.table.setItem(self.n, 2, description_item)
        units_item = QTableWidgetItem(amp.units)
        units_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(self.n, 3, units_item)
        
        self.n = self.table.rowCount()

    def getRow(self, i):
        row = []
        for r in range(self.table.columnCount() - 1):
            row.append(self.table.item(i, r).text())
        row.append(self.table.item(i, r+1).checkState())
        return row

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
        "err": QMessageBox.Icon.Critical,
        "info": QMessageBox.Icon.Information
    }
    dialog.setIcon(icons[message_type])
    dialog.setStandardButtons(QMessageBox.StandardButton.Ok)

    # Makes sure doesn't close until user closes it
    dialog.exec()

    return dialog

if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MeshMorpherGUI()
    with open("styles/styles.css", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())
    win.show()
    sys.exit(app.exec())
