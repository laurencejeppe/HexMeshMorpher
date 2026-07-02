# -*- coding: utf-8 -*-
"""
Classes and functions to deal with the visualisation of the MeshObjects. These
include wrappers for vtk and Qt
"""

import numpy as np
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
        self.renderer = vtk.vtkRenderer()
        self.AddRenderer(self.renderer)

        cam = self.renderer.GetActiveCamera()
        cam.SetParallelProjection(True)

        self.triad = None

    def setBackground(self, colour=[0.1, 0.2, 0.4]):
        """
        Set the background colour of the renderer
        
        colour: array_like
            The RGB values as floats of the background colour between [0, 1]
        """
        self.renderer.SetBackground(colour)

    def renderActor(self, actor, zoom=1.0):
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.renderer.GetActiveCamera().Zoom(zoom)
        self.Render()

    def addTriad(self, actor):
        lim = actor.GetBounds()
        transform = vtk.vtkTransform()
        transform.Translate(lim[0], lim[2], lim[4])
        scale = (lim[5] - lim[4]) * 0.1
        transform.Scale(scale, scale, scale)
        if self.triad:
            self.renderer.RemoveActor(self.triad)
        self.triad = vtk.vtkAxesActor()
        self.triad.SetUserTransform(transform)
        for ax in [self.triad.GetXAxisCaptionActor2D(),
                   self.triad.GetYAxisCaptionActor2D(),
                   self.triad.GetZAxisCaptionActor2D()]:
            ax.GetTextActor().GetTextProperty().SetFontFamilyToCourier()
            ax.GetTextActor().GetTextProperty().SetColor(0, 0, 0)
            ax.GetTextActor().GetTextProperty().ShadowOff()
            ax.GetTextActor().GetTextProperty().BoldOff()
            ax.GetTextActor().GetTextProperty().ItalicOff()
            ax.GetTextActor().GetTextProperty().SetFontSize(8)
        self.renderer.AddActor(self.triad)
        self.Render()

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

# Adapt the MeshActor class to work with all mesh objects, not just trimesh
# Or create a new mesh actor class that can handle inp meshes

class MeshActor(vtk.vtkActor):
    """
    This is an interface between the vtk window and the mesh objects.
    For a given input mesh this will pass all the necessary attributes to the vtk window
    """
    def __init__(self, input_mesh=None, CMap=None, bands=128):
        super().__init__()
        self.input_mesh = input_mesh
        self.mesh = vtk.vtkPolyData()
        self.points = vtk.vtkPoints()
        self.polys = vtk.vtkCellArray()
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputData(self.mesh)
        self.SetMapper(self.mapper)

        if input_mesh is not None and getattr(input_mesh, 'trimesh', None) is not None:
            self.setVert(input_mesh.trimesh.vertices)
            self.setFaces(input_mesh.trimesh.faces)
            normals = getattr(input_mesh.trimesh, 'vertex_normals', None)
            if normals is None:
                normals = getattr(input_mesh.trimesh, 'face_normals', None)
            self.setNorm(normals)

    def setVert(self, vert, deep=0):
        self._v = numpy_support.numpy_to_vtk(vert, deep=deep)
        self.points.SetData(self._v)
        self.mesh.SetPoints(self.points)
        self.mesh.Modified()

    def setFaces(self, faces, deep=0):
        faces = np.asarray(faces, dtype=np.int64)
        self._faces = np.c_[np.full((faces.shape[0], 1), faces.shape[1], dtype=np.int64), faces].ravel()
        self._f = numpy_support.numpy_to_vtkIdTypeArray(self._faces, deep=deep)
        self.polys.SetCells(len(faces), self._f)
        self.mesh.SetPolys(self.polys)
        self.mesh.Modified()

    def setNorm(self, norm, deep=0):
        if norm is None:
            return
        norm = np.asarray(norm, dtype=np.float32)
        if norm.shape[0] != self.mesh.GetNumberOfPoints():
            return
        self._n = numpy_support.numpy_to_vtk(norm, deep=deep)
        self.mesh.GetPointData().SetNormals(self._n)
        self.mesh.Modified()
        self.GetProperty().SetInterpolationToGouraud()

    def setObacity(self, opacity=1.0):
        self.GetProperty().SetOpacity(opacity)

    def setColour(self, colour=[1.0, 1.0, 1.0]):
        self.GetProperty().SetColor(colour)


class PointArrayActor(vtk.vtkActor):
    def __init__(self, point_array=None):
        self.points = vtk.vtkPoints()
        for p in point_array:
            self.points.InsertNextPoint(p)
        
        self.vertices = vtk.vtkCellArray()
        for i in range(len(point_array)):
            vertex = vtk.vtkVertex()
            vertex.GetPointIds().SetId(0, i)
            self.vertices.InsertNextCell(vertex)

        self.polydata = vtk.vtkPolyData()
        self.polydata.SetPoints(self.points)
        self.polydata.SetVerts(self.vertices)

        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputData(self.polydata)

        self.SetMapper(self.mapper)

        self.GetProperty().SetPointSize(8)

    def setColour(self, colour=[1.0, 0.0, 0.0]):
        self.GetProperty().SetColor(colour)

