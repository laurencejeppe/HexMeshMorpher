# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 19:29:14 2023

@author: ljr1e21
"""

import sys
import os
from PyQt6.QtCore import (Qt, pyqtSignal, QThread)
from PyQt6.QtGui import (QIcon, QAction)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog,
                             QVBoxLayout, QComboBox, QPushButton, QHBoxLayout,
                             QCheckBox, QTableWidget, QTableWidgetItem,
                             QGridLayout, QMessageBox, QLineEdit, QLabel,
                             QHeaderView, QDoubleSpinBox, QSpinBox,
                             QAbstractSpinBox, QStyle, QDialog, QProgressBar,
                             QTextEdit, QDialogButtonBox)
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
        self.open_mesh_btn = QPushButton("Open Mesh")
        self.open_mesh_btn.clicked.connect(self.load_stl_mesh)
        self.options_layout.addWidget(self.open_mesh_btn)
        self.save_mesh_btn = QPushButton("Save Mesh")
        self.save_mesh_btn.clicked.connect(self.save_meshes)
        self.options_layout.addWidget(self.save_mesh_btn)
        self.delete_mesh_btn = QPushButton("Delete Mesh")
        self.delete_mesh_btn.clicked.connect(self.delete_mesh)
        self.options_layout.addWidget(self.delete_mesh_btn)
        self.change_mesh_units_btn = QPushButton("Change Mesh Units")
        self.change_mesh_units_btn.clicked.connect(self.change_mesh_units)
        self.options_layout.addWidget(self.change_mesh_units_btn)
        self.find_landmarks_btn = QPushButton("Find Landmarks")
        self.find_landmarks_btn.clicked.connect(self.find_landmarks)
        self.options_layout.addWidget(self.find_landmarks_btn)

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
        self.openSTLmesh = QAction(QIcon('open.png'), 'Open TRI', self,
                                    triggered=self.load_stl_mesh)
        self.openINPmesh = QAction(QIcon("open.png"), 'Open INP', self,
                                   triggered=self.load_inp_mesh)
        self.choose_wdir = QAction(QIcon('open.png'), 'Choose Working Directory',
                                  self, triggered=self.choose_WDIR)
        self.saveFile = QAction(QIcon('open.png'), 'Save', self,
                                shortcut='Ctrl+S',
                                triggered=self.save_meshes)
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
        self.fileMenu.addAction(self.openSTLmesh)
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
        """ Opens the file dialog to select a file to open. """
        fname = QFileDialog.getOpenFileName(self,
                                            prompt,
                                            directory=self.WDIR,
                                            filter=type_filter)

        if fname[0] == '':
            return None
        return fname[0]

    def chooseSaveFile(self, type_filter: str, prompt: str='Save File'):
        """ Opens the file dialog to select a save location. """
        fname = QFileDialog.getSaveFileName(self,
                                            caption=prompt,
                                            directory=self.WDIR,
                                            filter=type_filter)

        if fname[0] == '':
            show_message("Mesh has not been saved!", title="Mesh Save Error")
            return None
        return fname[0]

    def choose_WDIR(self):
        _dir = QFileDialog.getExistingDirectory(self,
                                                'Select Directory',
                                                directory=self.WDIR)
        self.WDIR = _dir

    def save_meshes(self):
        if not self.file_manager.table.selectedItems():
            show_message(message="Please select a mesh in the table to change the units first!",
                         title="Item Selection Error")
        rows = []
        for item in self.file_manager.table.selectedItems():
            rows.append(self.file_manager.table.row(item))
        rows = set(rows)
        file_type_dict = {'stl':"MESH (*.stl)",
                          'inp':"ABAQUS (*.inp)"}
        for row in rows:
            item = self.file_manager.table.item(row, 0).text()
            item_type = self.file_manager.table.item(row, 1).text()
            f_path = self.chooseSaveFile(file_type_dict[item_type])
            if not f_path:
                return
            self.files[item].save_mesh(file_path=f_path)
            
    def load_mesh_dialog(self, stl=False, inp=False):
        stl_string = "MESH (*.stl)"
        inp_string = "ABAQUS (*.inp)"
        typestring_list = []
        if not stl and not inp:
            typestring = inp_string + ';; ' + stl_string
        else:
            if inp:
                typestring_list.append(inp_string)
            if stl:
                typestring_list.append(stl_string)
            ';; '.join(typestring_list)

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
            mesh = MeshObj.INPMesh(file_name, file_name, file_folder)
        elif file_path[-4:] == '.stl':
            mesh = MeshObj.STLMesh(file_name, file_name, file_folder)
        else:
            show_message("Mesh selection has failed")
            return

        self.open_mesh_dialog = Mesh_Options_Dialog(mesh, self)
        self.open_mesh_dialog.accepted.connect(self.add_mesh_to_file_manager)
        self.open_mesh_dialog.exec()

    def add_mesh_to_file_manager(self):
        mesh = self.open_mesh_dialog.retrieve_mesh_obj()
        mesh_name = mesh.f_name
        number = 0
        while mesh_name in self.files:
            number += 1
            mesh_name = mesh.f_name + f"-{number}"
        mesh.rename(mesh_name)
        self.files[mesh.f_name] = mesh
        mesh_obj = self.files[mesh.f_name]
        self.file_manager.addRow(mesh.f_name, mesh_obj)
        self.filesDrop.append(mesh.f_name)

    def load_stl_mesh(self):
        """
        This will open the load mesh dialog to select stl loading options.
        """
        self.load_mesh_dialog()

    def load_inp_mesh(self):
        """
        This will open the load mesh dialog to select inp loading options.
        """
        self.load_mesh_dialog()

    def change_mesh_units(self):
        if not self.file_manager.table.selectedItems():
            show_message(message="Please select a mesh in the table to change the units first!",
                         title="Item Selection Error")
        rows = []
        for item in self.file_manager.table.selectedItems():
            rows.append(self.file_manager.table.row(item))
        rows = set(rows)
        for row in rows:
            item = self.file_manager.table.item(row, 0).text()
            units = self.file_manager.table.item(row, 3).text()
            units = "mm" if units == "m" else "m"
            factor = 1000 if units == "m" else 0.001
            self.files[item].change_units(factor, units)
            self.file_manager.table.item(row, 3).setText(units)

    def delete_mesh(self):
        if not self.file_manager.table.selectedItems():
            show_message(message="Please select a mesh in the table to delete!",
                         title="Item Selection Error")
        rows = []
        for item in self.file_manager.table.selectedItems():
            rows.append(self.file_manager.table.row(item))
        rows = set(rows)
        for row in rows:
            item = self.file_manager.table.item(row, 0).text()
            self.files.pop(item)
            self.filesDrop.pop(row)
            self.file_manager.deleteRow(row)

    def run_amberg_mapping(self):
        self.amberg_nricp = Amberg_Mapping(self)
        self.amberg_nricp.show()

    def run_rbf_morpher(self):
        self.rbf_morpher = RBF_Morpher(self)
        self.rbf_morpher.show()

    def find_landmarks(self):
        if not self.file_manager.table.selectedItems():
            show_message(message="Please select a mesh in the table to add landmarks to!",
                         title="Item Selection Error")
            return
        rows = []
        for item in self.file_manager.table.selectedItems():
            rows.append(self.file_manager.table.row(item))
        rows = set(rows)
        if len(rows) > 1:
            show_message(message="Please only select one mesh to find landmarks!")
            return
        for row in rows:
            mesh_name = self.file_manager.table.item(row, 0).text()
        mesh = self.files[mesh_name]
        if not isinstance(mesh, MeshObj.STLMesh):
            show_message(message="Landmark finder is currently only supported \
                         for STL meshes!", title="Item Selection Error")
            return
        self.landmark_finder = LandmarkFinder(mesh=mesh, parent=self)
        self.landmark_finder.show()


class Mesh_Options_Dialog(QDialog):
    def __init__(self, mesh:MeshObj.Mesh, parent = None):
        super(Mesh_Options_Dialog, self).__init__(parent)

        self.mesh = mesh

        self.main_layout = QVBoxLayout()

        self.edits_layout = QGridLayout()
        self.name_text = QLabel("Name: ")
        self.name_edit = QLineEdit()
        self.file_type_text = QLabel("." + self.mesh.f_type)
        self.name_edit.setText(self.mesh.f_name)
        self.edits_layout.addWidget(self.name_text, 0, 0)
        self.edits_layout.addWidget(self.name_edit, 0, 1)
        self.edits_layout.addWidget(self.file_type_text, 0, 2)

        self.description_text = QLabel("Description: ")
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Add description")
        self.edits_layout.addWidget(self.description_text, 1, 0)
        self.edits_layout.addWidget(self.description_edit, 1, 1)

        self.main_layout.addLayout(self.edits_layout)

        self.unit_change_check_box = QCheckBox()
        if self.mesh.units == "mm":
            checkbox_string = "Convert mm to m"
        elif self.mesh.units == "m":
            checkbox_string = "Convert m to mm"
        self.unit_change_check_box.setText(checkbox_string)
        self.main_layout.addWidget(self.unit_change_check_box)

        self.convert_to_stl = QCheckBox()
        self.convert_to_stl.setText("Convert to STL")
        if mesh.f_type == "inp":
            self.main_layout.addWidget(self.convert_to_stl)

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttonBox)

        self.setLayout(self.main_layout)

        self.setWindowTitle(f"Load: {self.mesh.f_name}")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

    def retrieve_mesh_obj(self):
        self.mesh.rename(self.name_edit.text())
        description = self.description_edit.toPlainText()

        if self.unit_change_check_box.isChecked():
            if self.mesh.units == "mm":
                self.mesh.change_units(0.001, "m")
            elif self.mesh.units == "m":
                self.mesh.change_units(1000, "mm")

        if self.convert_to_stl.isChecked():
            self.mesh.write_stl()
            self.mesh = MeshObj.STLMesh(self.mesh.f_name, self.mesh.f_name, self.mesh.f_folder)

        description = self.description_edit.toPlainText()
        self.mesh.description = description

        return self.mesh

class Amberg_Mapping(QMainWindow):
    def __init__(self, parent = None):
        super(Amberg_Mapping, self).__init__(parent)
        self.setWindowTitle("Amberg Mapping")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
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
        self.use_faces.setChecked(True)
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

        # TODO: Have this as a pop up window that prevents you from doing
        # other things while the amberg mapping is taking place.
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0,1)
        self.layout.addWidget(self.progress_bar, 3, 0)

        self.main_widget.setLayout(self.layout)

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
        self.table.horizontalHeader() \
            .setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader() \
            .setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
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
            return
        source: MeshObj.STLMesh = self.files[self.source.currentText()]
        target: MeshObj.STLMesh = self.files[self.target.currentText()]
        assert source.units == target.units, "The source and target must have the same units!"
        description = f"Mapping from {self.source.currentText()} to {self.target.currentText()}"

        base_name = 'MappedMesh'
        output_name = base_name
        number = 0
        while output_name in self.parent.files:
            number += 1
            output_name = base_name + f'-{number}'

        output = MeshObj.STLMesh(output_name,
                                 output_name,
                                 f_folder=self.WDIR,
                                 description=description,
                                 load=False)
        output.set_units(source.units)
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

        if l:
            source_vertex_count = len(source.get_boundary())
            if target.boundary.interpollation_coords is not None and \
                target.boundary.interpollation_num == source_vertex_count:
                lpairs = [
                    [
                        source.boundary.nodes[i],
                        [target.boundary.interpollation_coords[i,j] for j in range(3)]
                    ]
                    for i in range(len(source.boundary.nodes))
                    ]
            else:
                self.use_landmarks.setChecked(False)
                show_message(message=f"Landmark pairs were selected, but no \
suitable landmark pairs were found!\nRun landmark finder \
with {source_vertex_count} boundary nodes on {target.f_name}")
                return
        else:
            lpairs = []

        options = {
            'gamma':g,
            'epsilon':e,
            'neighbors':n,
            'distance_threshold':d,
            'use_faces':f,
            'use_landmarks':l,
        }

        self.thread: AmbergThread = AmbergThread(source=source,
                                   target=target,
                                   output=output,
                                   steps=steps,
                                   options=options,
                                   callback=self.handle_result,
                                   lpairs=lpairs)
        self.progress_bar.setRange(0,0)
        self.thread.start()

    def handle_result(self, result:amberg_mapping.AmbergMapping):
        self.progress_bar.setRange(0,1)
        output_mesh = result.mapped
        self.parent.files[output_mesh.f_name] = output_mesh
        self.parent.file_manager.addRow(output_mesh.f_name, output_mesh)
        self.parent.filesDrop.append(output_mesh.f_name)
        self.close()

class AmbergThread(QThread):
    taskFinished = pyqtSignal(object)

    def __init__(self, source, target, output, steps, options, callback,
                 lpairs, parent=None):
        QThread.__init__(self, parent)
        self.taskFinished.connect(callback)
        self.source = source
        self.target = target
        self.output = output
        self.steps = steps
        self.options = options
        self.lpairs = lpairs

    def run(self):
        #lpairs = [[1, [0.0625779, -0.0421632, 0.0119162]], # Top Left
        #          [200, [-0.0636008, -0.0421502, 0.0119019]], # Top Right
        #          [10101, [0.0461566, -0.113105, -0.00230067]], # Bottom Left
        #          [10200, [-0.0484762, -0.113245, -0.00233835]]] # Bottom Right

        #lpairs = [[1, [0.0625774, 0.037793, 0.111964]],
        #          [200, [-0.0636172, 0.0377307, 0.111834]],
        #          [10101, [0.0461407, -0.0332396, 0.0977013]],
        #          [10200, [-0.0484672, -0.0332104, 0.0976772]]]

        AM = amberg_mapping.AmbergMapping(sourcey=self.source,
                                          targety=self.target,
                                          mappedy=self.output,
                                          steps=self.steps,
                                          options=self.options,
                                          lpairs=self.lpairs)
        self.taskFinished.emit(AM)

class RBF_Morpher(QMainWindow):
    def __init__(self, parent = None):
        super(RBF_Morpher, self).__init__(parent)
        self.setWindowTitle("RBF Morphing")
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.parent = parent
        self.files = parent.files
        self.WDIR = parent.WDIR

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

        self.use_multithread_check = QCheckBox("Use Multi-Thread RBF")
        self.main_layout.addWidget(self.use_multithread_check)

        self.run_morph_btn = QPushButton("Run Amberg Mapping")
        self.run_morph_btn.clicked.connect(self.initiate_morph)
        self.main_layout.addWidget(self.run_morph_btn)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0,1)
        self.main_layout.addWidget(self.progress_bar)

        self.mainWidget.setLayout(self.main_layout)

        self.resize(520,400)

    def initiate_morph(self):
        if self.unmapped.count() < 3:
            show_message(message="You need at least two meshes to perform an Amberg Mapping!",
                         title="Mesh Error")
            return
        unmapped: MeshObj.STLMesh = self.files[self.unmapped.currentText()]
        mapped: MeshObj.STLMesh = self.files[self.mapped.currentText()]
        morphee: MeshObj.Mesh = self.files[self.morphee.currentText()]

        use_multithread = self.use_multithread_check.isChecked()

        # Morph the nodes and replace them in the mesh objected
        self.thread: RBF_Thread = RBF_Thread(unmapped=unmapped,
                                             mapped=mapped,
                                             morphee=morphee,
                                             use_multithread=use_multithread,
                                             callback=self.handle_result)
        self.progress_bar.setRange(0,0)
        self.thread.start()

    def handle_result(self, result:MeshObj.Mesh):
        """ Handles the results from the RBF Thread. """
        self.progress_bar.setRange(0,1)
        old_name = result.f_name
        result.rename(f"{old_name}_RBF_Morph")
        self.parent.files[result.f_name] = result
        self.parent.file_manager.addRow(result.f_name, result)
        self.parent.filesDrop.append(result.f_name)
        self.close()

class RBF_Thread(QThread):
    """ Thread for processing RBF tasks. """
    taskFinished = pyqtSignal(object)

    def __init__(self, unmapped, mapped, morphee, use_multithread, callback,
                 parent=None):
        QThread.__init__(self, parent)
        self.taskFinished.connect(callback)
        self.unmapped = unmapped
        self.mapped = mapped
        self.morphee = morphee
        self.use_multithread = use_multithread

    def run(self):
        """ Starts the thread. """
        morpher: RBF_morpher.RBFMorpher \
            = RBF_morpher.RBFMorpher(self.unmapped,
                                     self.mapped,
                                     RBF_morpher.custom_RBF,
                                     use_multithread=self.use_multithread)
        nodes = morpher.morph_vertices(self.morphee.nodes[:,1:])
        self.morphee.update_nodes(nodes)

        self.taskFinished.emit(self.morphee)

class LandmarkFinder(QMainWindow):
    """ A class of QMainWindow that handles the automatic detection of
    boundary nodes in a mesh that could be used as langmark nodes in the
    amberg morphing algorithm. 
    
    The algorithms for this should potentially be within the MeshObj class.
    """
    def __init__(self, mesh:MeshObj.STLMesh, parent = None):
        super(LandmarkFinder, self).__init__(parent)
        self.setWindowTitle("Landmark Finder")
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.parent = parent

        self.mesh = mesh
        self.boundary_nodes = None

        self.main_layout = QGridLayout()
        self.mesh_name_label = QLabel(self.mesh.f_name)
        self.main_layout.addWidget(self.mesh_name_label, 0, 0)

        self.info_box = QLabel("")
        self.info_box.setWordWrap(True)
        self.main_layout.addWidget(self.info_box, 1, 0)

        self.button_layout = QVBoxLayout()
        self.evaluate_boundary_btn = QPushButton("Evaluate Mesh Boundary")
        self.evaluate_boundary_btn.clicked.connect(self.evaluate_boundary)
        self.button_layout.addWidget(self.evaluate_boundary_btn)
        self.resample_boundary_btn = QPushButton("Resmple Mesh Boundary")
        self.resample_boundary_btn.clicked.connect(self.resample_boundary_nodes)
        self.button_layout.addWidget(self.resample_boundary_btn)
        self.num_nodes_label = QLabel("Number of Resampled Nodes")
        self.button_layout.addWidget(self.num_nodes_label)
        self.num_nodes_selector = QSpinBox()
        self.num_nodes_selector.setRange(1, 1000)
        self.num_nodes_selector.setValue(76)        
        self.button_layout.addWidget(self.num_nodes_selector)
        self.ccw_flag = QCheckBox("Counter-Clockwise Resampling")
        self.button_layout.addWidget(self.ccw_flag)
        self.button_layout.addStretch()

        self.main_layout.addLayout(self.button_layout, 1, 1)


        self.main_widget.setLayout(self.main_layout)

        self.resize(520,400)

        # TODO: Change layout parameters to allow for the window to be bigger
        # without messing up the look

    def evaluate_boundary(self):
        """ Evaluates the boundary of the mesh and stores these parameters
        in the .boundary."""
        self.mesh.get_boundary()
        boundary_nodes = self.mesh.restarted_arranged_nodes(starting_point=[1.0, 1.0, 1.0])
        self.update_info_box("The mesh boundary has been evaluated:")
        self.update_info_box(f"\tDetected {len(self.mesh.boundary.nodes)} boundary nodes!")
        self.update_info_box(f"\tDetected {len(self.mesh.boundary.edges)} boundary edges!")
        self.update_info_box(f"\tDetected {len(self.mesh.boundary.corner_nodes)}" \
                             + " corners with a threshold of" \
                             + f" {self.mesh.boundary.corner_node_angle_threshold} degrees!")
        self.update_info_box(f"Corner nodes: {self.mesh.boundary.corner_nodes}")

    def resample_boundary_nodes(self):
        """ Resamples the boundary nodes to a given node count. """
        num_nodes = self.num_nodes_selector.value()
        self.mesh.resample_boundary_nodes(num_nodes, ccw_flag=self.ccw_flag.isChecked())
        self.update_info_box(f"Mesh boundary has been resampled to give \
                             coordinates of {num_nodes}.")

    def update_info_box(self, new_text):
        """ Adds a String to the info box to give a message about function completion to the user.

        Args:
            new_text (String): Message to be added to the info box display
        """
        info_box_text = self.info_box.text()
        info_box_text += (new_text + '\n')
        self.info_box.setText(info_box_text)


class progressBar(QMainWindow):
    def __init__(self, parent = None) -> None:
        super(progressBar).__init__(parent)
        # TODO: Set this up to be a pop up window that comes up when the
        # amberg or RBF morphers are running the program to prevent the user
        # from doing anything else with the application.
        pass



class fileManager(QWidget):
    """
    Controls to manage the displayed files.
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
        self.table.horizontalHeader() \
            .setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader() \
            .setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader() \
            .setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
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
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(self.n, 0, name_item)
        f_type_item = QTableWidgetItem(amp.f_type)
        f_type_item.setFlags(f_type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        f_type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(self.n, 1, f_type_item)
        description_item = QTableWidgetItem(amp.description)
        description_item.setFlags(description_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(self.n, 2, description_item)
        units_item = QTableWidgetItem(amp.units)
        units_item.setFlags(units_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        units_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(self.n, 3, units_item)

        self.n = self.table.rowCount()

    def deleteRow(self, row):
        self.table.removeRow(row)
        self.n = self.table.rowCount()

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
    with open("src/HexMeshMorpher/styles/styles.css", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())
    win.show()
    sys.exit(app.exec())
