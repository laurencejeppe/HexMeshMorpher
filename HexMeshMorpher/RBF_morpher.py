from HexMeshMorpher import MeshObj
import time
from multiprocessing import Process, Queue, Lock, Array
import queue
import numpy as np
import os

class RBFMorpher:
    """Class that handles the interpolation of the displacement field
    defined by the mapping of some source nodes (vetices). The radial
    basis function (RBF) is hard-coded in this class, but that may be
    changed later."""
    def __init__(self, original_mesh: MeshObj.STLMesh,
                 displaced_mesh: MeshObj.STLMesh,
                 RBF,
                 use_multithread: bool=False,
                 processors: int=6):

        self.RBF = RBF
        self.use_multithread = use_multithread
        self.processors = processors

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
        """Generates interpolation matrix for transformation field."""
        start_time = time.time()
        print("Generating Interpolation Matrix")

        # Compute pairwise Euclidean distances in a vectorized way
        V = self.original_source_vertices  # shape: (n, d)
        diffs = V[:, np.newaxis, :] - V[np.newaxis, :, :]  # shape: (n, n, d)
        distances = np.sqrt(np.sum(diffs ** 2, axis=-1))   # shape: (n, n)

        # Apply RBF function element-wise to the distance matrix
        self.interp_matrix = self.RBF(distances) # assumes RBF accepts ndarray input

        print("Successfully Generated Interpolation Matrix in {:.2f}s".format(time.time() - start_time))

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
        """Generates matrix of coefficients for the transformation field."""
        import time
        start_time = time.time()
        print("Generating Coefficient Matrix")

        # Solve interp_matrix * X = source_v_disp for X
        self.coeff_matrix = np.linalg.solve(self.interp_matrix, self.source_v_disp)

        print("Successfully Generated Coefficient Matrix in {:.2f}s".format(time.time() - start_time))

    def calculate_displacements(self, points):
        """Calculates the individual displacements required by morph_vertices."""
        n_points = len(points)
        print("Calculating Displacements of "+str(n_points)+" points")
        start_time = time.time()

        if self.use_multithread:
            lock = Lock()
            displacement_x = Array('f', n_points)
            displacement_y = Array('f', n_points)
            displacement_z = Array('f', n_points)
            number_of_tasks = self.n
            number_of_processes = self.processors
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
                    l = [ x for x in range(i*verts_per_process, verts_per_process*(i + 1))]
                tasks_to_do.put(l)

            print(f'{number_of_tasks} to be completed')

            # creating processes
            print(f'Creating {number_of_processes} processes')
            for w in range(number_of_processes):
                p = Process(target=self.do_job,
                            args=(tasks_to_do, tasks_done, points,
                                  displacement_x, displacement_y,
                                  displacement_z, lock))
                processes.append(p)
                p.start()

            # completing process
            print('Waiting for processes to finish')
            for p in processes:
                p.join()

            # collecting results
            print('Getting output from processes')
            while not tasks_done.empty():
                print(f'Processing {tasks_done.get()}!')

            displacements = [
                [displacement_x[i], displacement_y[i], displacement_z[i]]
                for i in range(n_points)
                ]

            print("Displacements Successfully Calculated in "+str(time.time()-start_time)+"s")
            return displacements

        else:
            # Non parallel calculation
            displacements = np.zeros((n_points, 3))
            for vertex_index in range(self.n):
                displacements += self._disp_calculation(vertex_index, points)

        print("Displacements Successfully Calculated in "+str(time.time()-start_time)+"s")
        return displacements

    def do_job(self, tasks_to_do, tasks_done, points, displacement_x,
               displacement_y, displacement_z, lock):
        """ Function for multithreading task. """
        while True:
            try:
                task = tasks_to_do.get_nowait()
                print(task)

                if task == 'TERMINATE':
                    tasks_to_do.put(task)
                    break

                disp = np.zeros((len(points), 3))
                for vertex_index in task:
                    disp += self._disp_calculation(vertex_index, points)
                print("Displacements Caculated for: ", os.getpid())
                with lock:
                    displacement_x[:] = displacement_x[:] + disp[:,0]
                    displacement_y[:] = displacement_y[:] + disp[:,1]
                    displacement_z[:] = displacement_z[:] + disp[:,2]
                print(f"Process {os.getpid()} is finished.")
                tasks_done.put(f'Task {int(task[0]/100)} is finished!')
            except queue.Empty:
                break
            else:
                print(f'Task {int(task[0]/100)} is finished!')
                time.sleep(.5)
        return True

    def _disp_calculation(self, vertex_index, points):
        disps = np.zeros((len(points), 3))
        for i, point in enumerate(points):
            source_vertex = self.original_source_vertices[vertex_index]
            diff_vec = point - source_vertex
            disps[i] = self.coeff_matrix[vertex_index] * self.RBF(self.__magnitude(diff_vec))
        return disps

    def morph_vertices(self, points):
        """Takes a set of points and morphes them according to the transformation matix in self."""
        displacements = self.calculate_displacements(points)
        new_vertices = np.zeros(np.shape(points))
        for i, point in enumerate(points):
            new_vertices[i] = np.add(point, displacements[i])
        return new_vertices


def custom_RBF(r):
    return r
