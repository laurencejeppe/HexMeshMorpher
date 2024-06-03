"""
This is the adapted code from Pauls MeshMorphPy algorithm for morphing 3D
meshes. The addaptations mostly revolve around using mesh objects that can
include meshes from imp files and does not rely too heavily on the trimesh
objects for all the mrophing.
"""
import sys
import os

import time
import numpy as np
import trimesh as tr
import pyvista as pv
from multiprocessing import Process, Queue, Lock, Array
import queue

WDIR = 'D:/ljr1e21/Documents/TIDAL Network+ Project/'
os.chdir(WDIR)

sys.path.append(os.path.join(WDIR, 'Code'))

from General import MeshObj

FOLDER = 'Liner Model'
LINER_RIM_Y = 200.0

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

class AmbergMapping:
    """
    Performs amberg non-rigid ICP on the trimesh objects of source and target
    objects and returns to the mapping in the mapped object which is
    returned.
    """
    def __init__(self, sourcey: MeshObj.STLMesh, targety: MeshObj.STLMesh, mappedy: MeshObj.STLMesh,
                 lpairs: list=None, steps: list=None,
                 gamma: int=1) -> None:
        self.source = sourcey
        self.target = targety
        self.mapped = mappedy
        self.gamma = gamma
        self.steps = steps
        if not self.steps:
            self.steps = [
                [0.01, 10, 0.5, 10],
                [0.02, 5, 0.5, 10],
                [0.03, 2.5, 0.5, 10],
                [0.01, 0, 0.0, 10],
            ]

        # Landmark picking variables
        self.landmark_pairs = []
        self.picking_buffer = []
        if lpairs:
            self.landmark_pairs = lpairs # [source vertex index, target vertex position vector]

        self.run_amberg()

    def run_amberg(self):
        """Runs the amberg mapping."""
        if self.landmark_pairs:
            source_indices = [pair[0] for pair in self.landmark_pairs]
            target_points = [pair[1] for pair in self.landmark_pairs]

            start_time = time.time()
            print("Performing Amberg Mapping")
            morphed_vertices \
                = tr.registration.nricp_amberg(self.source.trimesh,
                                                self.target.trimesh,
                                                use_faces=True, # Changing to True causes error (installed rtree with pip to solve)
                                                source_landmarks=source_indices,
                                                target_positions=target_points,
                                                steps=self.steps,
                                                gamma=self.gamma,
                                                eps=0.000001, # 0.0001 default
                                                neighbors_count=3, # 8 default
                                                distance_threshold=0.1) # 0.1 default
            self.mapped.trimesh = tr.Trimesh(vertices=morphed_vertices,
                                                faces=self.source.trimesh.faces)
            print("Amberg Mapping Completed in " + str(time.time() - start_time) + "s")
        else:
            start_time = time.time()
            print("Performing Amberg Mapping")
            morphed_vertices = tr.registration.nricp_amberg(self.source.trimesh,
                                                            self.target.trimesh,
                                                            use_faces=True, # Changing to True causes error (installed rtree with pip to solve)
                                                            steps=self.steps,
                                                            gamma=self.gamma,
                                                            eps=0.000001, # 0.0001 default
                                                            neighbors_count=3, # 8 default
                                                            distance_threshold=0.1) # 0.1 default
            self.mapped.trimesh = tr.Trimesh(vertices=morphed_vertices,
                                             faces=self.source.trimesh.faces)
            print("Amberg Mapping Completed in "+str(time.time()-start_time)+"s")

    def find_vertex_index(self, mesh: MeshObj.STLMesh, vertex):
        """Finds the index of a vertex in the mesh [mesh_name] given its position."""
        for i, mesh_vertex in enumerate(mesh.trimesh.vertices):
            if (mesh_vertex == vertex).all():
                return i

def custom_RBF(r):
    return r

class RBFMorpher:
    """Class that handles the interpolation of the displacement field
    defined by the mapping of some source nodes (vetices). The radial
    basis function (RBF) is hard-coded in this class, but that may be
    changed later."""
    def __init__(self, original_mesh: MeshObj.STLMesh, displaced_mesh: MeshObj.STLMesh, RBF):

        self.RBF = RBF

        self.original_source_vertices = np.array(original_mesh.trimesh.vertices)
        self.source_v_disp = np.array(displaced_mesh.trimesh.vertices)-self.original_source_vertices

        self.n = len(self.original_source_vertices)

        self.interp_matrix = np.zeros((self.n,self.n))

        self.coeff_matrix = None

        self.generate_interpolation_matrix()
        self.generate_coefficient_matrix()

    def __magnitude(self, vector):
        return np.sqrt(vector.dot(vector))

    def generate_interpolation_matrix(self):
        """Generates inperpolation matrixs for transformation field."""
        start_time = time.time()
        print("Generating Interpolation Matrix")
        for i in range(0, self.n):
            for j in range(0, self.n):
                self.interp_matrix[i][j] \
                    = self.RBF(self.__magnitude(self.original_source_vertices[i] \
                                                - self.original_source_vertices[j]))
        print("Successfuly Generated Interpolation Matrix in "+str(time.time()-start_time)+"s")

    def save_interpolation_matrix(self, file_name):
        """Saves inperpolation matrixs as a npy file."""
        np.save(file_name, self.interp_matrix)

    def load_interpolation_matrix(self, file_name):
        """Loads existing inperpolation matrix for transformation field."""
        start_time = time.time()
        print("Loading Interpolation Matrix")
        self.interp_matrix = np.load(file_name)
        print("Interpolation Matrix Loaded Successfully in "+str(time.time()-start_time)+"s")

    def generate_coefficient_matrix(self):
        """Generates matrix of coefficients for the transfomoation field."""
        start_time = time.time()
        print("Generating Coefficient Matrix")
        coeff_matrix = np.linalg.inv(self.interp_matrix)@self.source_v_disp
        print(("Successfuly Generated Coefficient Matrix in "+str(time.time()-start_time)+"s"))
        self.coeff_matrix = coeff_matrix

    def calculate_displacements(self, points, parrallel:bool=False, processors:int=4):
        """Calculates the individual displacements required by morph_vertices."""
        n_points = len(points)
        print("Calculating Displacements of "+str(n_points)+" points")
        start_time = time.time()

        if parrallel:
            lock = Lock()
            displacement_x = Array('f', n_points, lock=lock)
            displacement_y = Array('f', n_points, lock=lock)
            displacement_z = Array('f', n_points, lock=lock)
            number_of_tasks = self.n
            number_of_processes = processors
            processes = []

            # instantiating a queue object
            tasks_to_do = Queue()
            tasks_done = Queue()

            verts_per_process = 100
            print('Creating Task List')
            for i in range(int(np.ceil(number_of_tasks/100))):
                if i*100 + 99 > number_of_tasks:
                    l = [ x for x in range(i*100, number_of_tasks)]
                else:
                    l = [ x for x in range(i*verts_per_process, verts_per_process*(i + 1) - 1)]
                tasks_to_do.put(l)

            print(f'{number_of_tasks} to be completed')

            # creating processes
            print(f'Creating {number_of_processes} processes')
            for w in range(number_of_processes):
                p = Process(target=self.do_job, args=(tasks_to_do, tasks_done, points, displacement_x, displacement_y, displacement_z, lock))
                processes.append(p)
                p.start()

            # completing process
            print('Waiting for processes to finish')
            for p in processes:
                p.join()
        

            # collecting results
            print('Getting output from processes')
            while not tasks_done.empty():
                print(f'Processing {int(tasks_done.get())}!')

            displacements = [ [displacement_x[i], displacement_y[i], displacement_z[i]] for i in range(n_points)]

            print("Displacements Successfully Calculated in "+str(time.time()-start_time)+"s")
            return displacements

        else:
            # Non parallel calculation
            displacements = np.zeros((n_points, 3))
            for vertex_index in range(0, self.n):
                displacements += self._disp_calculation(vertex_index, points)

        #displacements = np.zeros((n_points, 3))
        #for vertex_index in range(0, self.n):
        #    for point_index in range(0, n_points):
        #        point = points[point_index]
        #        source_vertex = self.original_source_vertices[vertex_index]
        #        diff_vec = point-source_vertex
        #        displacements[point_index] \
        #            += self.coeff_matrix[vertex_index] * self.RBF(self.__magnitude(diff_vec))

        print("Displacements Successfully Calculated in "+str(time.time()-start_time)+"s")
        print(displacements)
        return displacements

    def do_job(self, tasks_to_do, tasks_done, points, displacement_x, displacement_y, displacement_z, lock):
        while True:
            try:
                task = tasks_to_do.get_nowait()

                if task == 'TERMINATE':
                    tasks_to_do.put(task)
                    break

                disp = np.zeros((len(points), 3))
                for vertex_index in task:
                    disp += self._disp_calculation(vertex_index, points)
                with lock:
                    displacement_x.value = displacement_x.value + disp[:,0]
                    displacement_y.value = displacement_y.value + disp[:,1]
                    displacement_z.value = displacement_z.value + disp[:,2]
                tasks_done.put(f'Task {int(task[0]/100)} is finished!')
            except queue.Empty():
                break
            else:
                print(f'Task {int(task[0]/100)} is finished!')
                time.sleep(.5)
        return True

    def _disp_calculation(self, vertex_index, points):
        disps = np.zeros((len(points), 3))
        for i, point in enumerate(points):
            source_vertex = self.original_source_vertices[vertex_index]
            diff_vec = point-source_vertex
            disps[i] = self.coeff_matrix[vertex_index] * self.RBF(self.__magnitude(diff_vec))
        return disps

    def morph_vertices(self, points):
        """Takes a set of points and morphes them according to the transformation matix in self."""
        displacements = self.calculate_displacements(points)
        new_vertices = np.zeros((len(displacements), 3))
        for i, point in enumerate(points):
            new_vertices[i] = point + displacements[i]
        return new_vertices


def plot_meshes(meshes):
    """Plots the meshes that are contained withing meshes"""
    plot = MeshPlotter()

    for mesh in meshes:
        plot.plot_in_colour(mesh)

    plot.show_axes()
    plot.show_grid()
    plot.show_plot()
