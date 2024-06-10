# -*- coding: utf-8 -*-
"""
Created on Wed Apr  5 19:29:14 2023

@author: ljr1e21
"""

import fnmatch as fnm
import sys
import os
from dataclasses import dataclass
from PyQt6.QtGui import (QIcon, QAction)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog,
                             QVBoxLayout, QComboBox, QPushButton, QHBoxLayout,
                             QCheckBox)
import MeshObj

class MeshMorpherGUI(QMainWindow):
    def __init__(self):
        super(MeshMorpherGUI,self).__init__()

        self.setWindowTitle("MeshMorphPy")

        self.WDIR = os.path.join(os.getcwd(), 'Meshes')
        os.makedirs(self.WDIR)

        self.initUI()

    def initUI(self):
        self.mainWidget = QWidget()
        self.setCentralWidget(self.mainWidget)
        self.createActions()
        self.createMenus()

        self.layout = QVBoxLayout()

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
        self.resize(200,200)
        self.show()


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

    def createActions(self):
        self.openFile = QAction(QIcon('open.png'), 'Open', self,
                                shortcut='Ctrl+O',
                                triggered=self.chooseOpenFile)
        self.openQUADmesh = QAction(QIcon('open.png'), 'Open QUAD', self,
                                    triggered=self.load_quad_mesh('QUAD_Mesh'))
        self.choose_wdir = QAction(QIcon(122), 'Choose Working Directory',
                                  self, triggered=self.choose_WDIR)
        self.saveFile = QAction(QIcon('open.png'), 'Save', self,
                                shortcut='Ctrl+S',
                                triggered=self.chooseSaveFile)
        self.exitAct = QAction("E&xit", self, shortcut="Ctrl+Q",
                               triggered=self.close)


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

    def choose_WDIR(self):
        _dir = QFileDialog.getExistingDirectory(self,
                                                'Select Directory',
                                                directory=self.WDIR)
        self.WDIR = dir

    def write_inp(self):
        self.title = self.inp_file.split('/')[-1][:-4]
        # Creating inp file
        self.nod_head = '*NODE\n'
        self.ell_head = '*ELEMENT, TYPE=' + self.element_type_CB.currentText() + ', ELSET=PT_' + self.title + '\n'

        for i, _set in enumerate(self.sets):
            self.sets[i].el_type = self.element_type_CB.currentText()

        # Open/Create new inp file and write main heading
        with open(self.inp_file, 'w', encoding='utf-8') as output:

            for _set in self.sets:
                output.write(_set.mat_head())

            # Write node data
            self.writeNodeData(output, self.nod_head, self.NODE_DATA)

            # Write element data
            for _set in self.sets:
                output.write(_set.get_elset_output())

            # Write the nodeset data
            for _set in self.sets:
                output.write(_set.get_nset_output())

        print('Successfully written .inp file!')

    def NUMOFF(self, ellnod):
        # ellnod is string with 'NODE' for node count or 'ELEM' for element count
        Index = self.findIndex('NUMOFF,' + ellnod)
        NUMOFF = int(self.cdb_list[Index[0]].split(',')[-1].strip())
        return NUMOFF

    def findIndex(self, key_word_input):
        """Finds the index of the occurances of a specified keyword."""
        wildcard = '*'
        Instance = fnm.filter(self.cdb_list, key_word_input + wildcard)
        Index = []
        if len(Instance) > 0:
            for instance in Instance:
                Index.append(self.cdb_list.index(instance))
            return Index
        else:
            print('No ' + key_word_input + ' found, check the output file for completeness!')
            return

    def writeNodeData(self, output, header, DATA):
        output.write(header)
        count = 0
        for i, D in enumerate(DATA):
            for j, d in enumerate(D):
                if DATA[i][j] == '':
                    DATA[i][i] = '0.0000000000000E+000'
                    print(DATA[i])
                    count += 1
                if self.convertUnits.checkState() and j > 0:
                    d = self.convertString_mm_to_m(d)
                output.write(d)
                if j != len(DATA[0])-1:
                    output.write(',')
            output.write('\n')

    def convertString_mm_to_m(self, string):
        print(string)
        l = string.split('.')
        print(l)
        l1 = l[0] + l[1][0:3]
        l2 = l[1][3:]
        return l1 + '.' + l2

    @dataclass
    class Set:
        """Class for holding the data for an element set.
        Data is a dictionary with the element number as the key and list of
        corresponding nodes as the data."""
        name: str
        el_type: str = None
        el_data: dict = None
        nodes: list = None

        def get_elset_output(self) -> str:
            """Creates the string to be written to the output file for the element set."""
            _list = []
            _list.append(f'*ELEMENT, TYPE={self.el_type}, ELSET={self.name}\n')
            for element in self.el_data:
                line = f"{element}, {', '.join(self.el_data[element])}\n"
                _list.append(line)
            return ''.join(_list)

        def get_nset_output(self) -> str:
            """Creates string to be written to the output file for the node set."""
            _list = []
            _list.append(f'*NSET, NSET={self.name}, internal')
            num_lines = round((len(self.nodes) / 16) + 1)
            x = 1
            for i in range(num_lines):
                if i == num_lines - 1:
                    x = 0
                string = ', '.join(self.nodes[i*16:(i*16+16+1)*x-1])
                _list.append(string)
            return '\n'.join(_list) + '\n'
        
        def get_nodes(self) -> None:
            for element in self.el_data:
                for node in self.el_data[element]:
                    self.nodes.append(node)
            self._remove_duplicate_nodes()

        def _remove_duplicate_nodes(self) -> None:
            self.nodes =  list( dict.fromkeys(self.nodes) )
            for element in self.el_data:
                self.el_data[element] = list( dict.fromkeys(self.el_data[element]))

        def mat_head(self) -> str:
            return f'*SOLID SECTION, ELSET={self.name}, MATERIAL=PM_{self.name}\n*MATERIAL, NAME=PM_{self.name}\n'


    def load_quad_mesh(self, mesh_name: str) -> MeshObj.STLMesh:
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
        file_name = fname[0]

        if file_name[-4:] == '.inp':
            # Load liner surface inp file
            liner_surface_inp = MeshObj.LinerINPMesh(mesh_name, mesh_name,
                                                     os.path.join(self.WDIR, mesh_name),
                                                     description='Unmorphed liner inp surface mesh')
            liner_surface_inp.write_stl()   # Save as stl
            # Load liner surface stl file
            liner_s = MeshObj.STLMesh(mesh_name, mesh_name,
                                      os.path.join(self.WDIR, mesh_name),
                                      description='Unmorphed liner surface mesh')
        elif file_name[-4:] == '.stl':
            # Load liner surface stl file
            liner_s = MeshObj.STLMesh(mesh_name, mesh_name,
                                      os.path.join(self.WDIR, mesh_name),
                                      description='Unmorphed liner surface mesh')
        else:
            return
        return liner_s



if __name__=="__main__":
    app = QApplication(sys.argv)
    win = MeshMorpherGUI()
    win.show()
    sys.exit(app.exec())
