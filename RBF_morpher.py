
import MeshObj
import time
from multiprocessing import Process, Queue, Lock, Array
import queue
import numpy as np

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


def custom_RBF(r):
    return r
