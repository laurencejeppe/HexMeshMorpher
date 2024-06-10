"""
TODO: Complete this docstring
"""
import pyvista as pv
import numpy as np
import MeshObj


class MeshPlotter:
    """Class to handle and deal with the plotting of different meshes.
    This class makes it easy to keep all the plotted meshes in one place
    and makes it easy to keep the mesh logic separate from the visulation stuff."""
    def __init__(self):
        self.actors = {}
        self.light_skin_tone = [246,171,142]
        self.tendon_blue = [51,204,255]

        self.pl = pv.Plotter()

    def plot_mesh(self, mesh: MeshObj.STLMesh, colour, scalars=None, cmap=None,
                  opacity=1, scale_bar_args=None, clim=None):
        """Plots all of the vertices in a mesh as spheres in the pyvista plotter window.
        
        mesh_collection: the mesh collection object that contains the mesh
        mesh_name: the name/key of the mesh within the mesh collection's meshes dictionary
        colour: the colour you wish each point/vertex in the plot to be"""

        mesh_vertices = mesh.trimesh.vertices
        self.actors[mesh.name] = self.pl.add_points(pv.PolyData(mesh_vertices),
                                                    color=colour,
                                                    name=mesh.name,
                                                    render_points_as_spheres=True,
                                                    scalars=scalars,
                                                    cmap=cmap,
                                                    opacity=opacity,
                                                    scalar_bar_args=scale_bar_args,
                                                    clim=clim)

    def plot_mesh_slice(self, mesh: MeshObj.STLMesh, colour, start, end, plot_name):
        """EXPERIMENTAL FUNCTION
        Plots only a slice of the vertices in a mesh..."""
        mesh_vertices = mesh.trimesh[start:end]
        self.actors[plot_name] = self.pl.add_points(pv.PolyData(mesh_vertices),
                                                    color=colour,
                                                    name=plot_name,
                                                    render_points_as_spheres=True,
                                                    point_size=6)

    def show_axes(self):
        self.pl.add_axes(line_width = 5)

    def show_grid(self):
        self.pl.show_grid()

    def show_plot(self):
        self.pl.show()

    #EXPERIMENTAL FEATURES
    def plot_in_colour(self, mesh: MeshObj.STLMesh, colour="white", opacity=1,
                       show_edges=False):
        self.actors[mesh.name] = self.pl.add_mesh(mesh.trimesh,
                                                  color=colour,
                                                  opacity=opacity,
                                                  name=mesh.name,
                                                  show_edges=show_edges)

    def add_text(self, actor_name, text, location = 'upper_left', colour = "black"):
        self.actors[actor_name] = self.pl.add_text(text,
                                                   name=actor_name,
                                                   position=location,
                                                   color=colour)

    def plot_nodes_by_indices(self, mesh: MeshObj.STLMesh, indices, colour, size = 10):
        vertices = [mesh.trimesh.vertices[index] for index in indices]
        self.pl.add_points(np.array(vertices), color=colour, point_size = size)

    def plot_point(self, position, colour, size = 10):
        self.pl.add_points(np.array(position), color=colour, point_size = size)



def plot_meshes(meshes):
    """Plots the meshes that are contained withing meshes"""
    plot = MeshPlotter()

    for mesh in meshes:
        plot.plot_in_colour(mesh)

    plot.show_axes()
    plot.show_grid()
    plot.show_plot()
