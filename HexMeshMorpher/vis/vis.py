# -*- coding: utf-8 -*-
"""
Classes and functions to deal with the visualisation of the MeshObjects. These
include wrappers for vtk and Qt
"""

import numpy
import vtk
from vtk.util import numpy_support
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
vtk.vtkObject.GlobalWarningDisplayOff()

class vtkRenWin(vtk.vtkRenderWindow):
    """
    This window can be either used on it's own, or embedded within a Qt Window.
    """
    def __init__(self):
        super().__init__()

class qtVtkWindow(QVTKRenderWindowInteractor):
    """
    This provides the interface between Qt and the vtkRenWin
    """
    def __init__(self):
        super().__init__(rw=vtkRenWin())
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.SetInteractorStyle(self.style)
        self.iren = self._RenderWindow.GetInteractor()
        self.iren.Initialize() 