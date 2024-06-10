# -*- coding: utf-8 -*-
"""
Created on Wed Mar 06 12:31:00 2024

@author: ljr1e21
"""

import os
import fnmatch as fnm
import numpy as np
import trimesh as tr
import pymeshlab as ml

FOLDER = 'Geometry'

class Mesh():
    """Class for containing all the information common between meshes"""
    def __init__(self, name: str, f_name: str, f_type: str, f_folder: str, description: str=None) -> None:
        self.name = name
        self.f_name = f_name
        self.description = description
        self.f_type = f_type
        self.f_folder = f_folder
        self.f_path = self.path()

    def path(self, file_name: str=None, file_type: str=None):
        """Generates the path of the mesh object depending on the f_name and f_type"""
        f_name = file_name if file_name else self.f_name
        f_type = file_type if file_type else self.f_type
        return os.path.join(self.f_folder, f_name + '.' + f_type)

    def rename(self, file_name: str, file_folder: str=None):
        """Renames the mesh and updates self.f_path."""
        self.f_name = file_name
        self.f_folder = file_folder if file_folder else self.f_folder
        self.f_path = self.path()

def rot_x(ang):
    """Returns transformation matrix for rotations of ang (deg) about the x axis"""
    ang = ang*np.pi/180
    return np.array([[1, 0, 0, 0],
                     [0, np.cos(ang), -np.sin(ang), 0],
                     [0, np.sin(ang), np.cos(ang), 0],
                     [0, 0, 0, 1]])

def rot_y(ang):
    """Returns transformation matrix for rotation of ang (deg) about y axis"""
    ang = ang*np.pi/180
    return np.array([[np.cos(ang), 0, np.sin(ang), 0],
                     [0, 1, 0, 0],
                     [-np.sin(ang), 0, np.cos(ang), 0],
                     [0, 0, 0, 1]])

def rot_z(ang):
    """Returns transformation matrix for rotation of ang (deg) about z axis"""
    ang = ang*np.pi/180
    return np.array([[np.cos(ang), -np.sin(ang), 0, 0],
                     [np.sin(ang), np.cos(ang), 0, 0],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])

def translation_matrix(vector):
    """Returns transformation matrix for a translation of x, y and z for vector = [x, y, z]"""
    return np.array([[1, 0, 0, vector[0]],
                     [0, 1, 0, vector[1]],
                     [0, 0, 1, vector[2]],
                     [0, 0, 0, 1]])

def scaling_matrix(scale):
    """Returns transformation matrix for a uniform scalling of x, y and z by a factor of scale."""
    return np.array([[scale, 0, 0, 0],
                     [0, scale, 0, 0],
                     [0, 0, scale, 0],
                     [0, 0, 0, 1]])

class STLMesh(Mesh):
    """Class for defining file names and locations where they are saved"""
    def __init__(self, name: str, f_name: str, f_folder: str, description: str=None, load: bool=True) -> None:
        Mesh.__init__(self, name, f_name, 'stl', f_folder, description)

        self.trimesh = None

        if load:
            self.load_stl()

    def load_stl(self) -> None:
        """Loads STL file as trimesh object."""
        self.trimesh = tr.load_mesh(self.path())

    def save_trimesh_as_stl(self, name=None) -> None:
        """Saves trimesh object as an STL."""
        self.trimesh.export(self.path(name))
        print(f"File successfully saved as {self.path(name)}")

    def save_trimesh_as_npy(self) -> None:
        """A function that saves a trimeshe's vertices and faces in npy files. This was implemented
        before the STL saving feature. It may still be useful in some instances, so it will be left
        here."""
        vertices = self.trimesh.vertices
        faces = self.trimesh.faces
        np.save("vert_" + self.f_name, vertices)
        np.save("faces_" + self.f_name, faces)

    def load_trimesh_from_npy(self) -> None:
        """A function to load trimeshes meshes that have been saved as npy files."""
        print("LOADING: " + self.f_name)
        loaded_vertices = np.load("vert_" + self.f_name)
        loaded_faces = np.load("faces_" + self.f_name)
        self.trimesh = tr.Trimesh(loaded_vertices, loaded_faces)
        print("LOADED: " + self.f_name)

    def apply_transformation(self, t_matrix) -> None:
        """Apply transformation matrix to the trimesh object"""
        self.trimesh.apply_transform(t_matrix)

    def copy_mesh(self, new_name: str, new_f_name: str, new_description: str=None):
        """Returns a new STMesh object with the same trimesh"""
        mesh = STLMesh(new_name, new_f_name, self.f_folder, new_description, load=False)
        mesh.trimesh = self.trimesh.copy()
        return mesh

    def cut_mesh(self, plane_axis: int=0, plane_offset: float=0.0,
                 polygon: bool=False, section: int=None, custom_axis=None) -> None:
        """
        Uses pymeshlab to cut the mesh into two pieces with a plane
        perpendicular to plane_axis at on offset of plane_offset.
        Arguments:
            plane_axis: int
                0 -> X Axis (YZ Plane)
                1 -> Y Axis (XZ Plane)
                2 -> Z Axis (XY Plane)
            plane_offset: float
            polygon: bool
                If true saves polygon resulting from slice as a polygon .ply file
            section: int
                If true saves section resulting from slice as new .stl file
                1 -> First section resulting from slice
                2 -> Second section resulting from slice
        Returns: 
            None
        """
        self.save_trimesh_as_stl()

        ms = ml.MeshSet()
        ms.load_new_mesh(self.f_path)
        ms.generate_polyline_from_planar_section(planeaxis=plane_axis,
                                                 planeoffset=plane_offset,
                                                 splitsurfacewithsection=True,
                                                 customaxis=custom_axis)

        if polygon:
            ms.set_current_mesh(1)
            ms.save_current_mesh(self.path(self.f_name + 'Polygon', 'ply'),
                                 binary=False)

        if section:
            mesh_num = 2 if section == 1 else 3
            ms.set_current_mesh(mesh_num)
            ms.save_current_mesh(self.path(self.f_name + '_cut'))

    def get_boundary_nodes(self) -> dict:
        """Take a trimesh object as input and returns the coordinates of all the
        nodes that are on a boundary of the mesh. It is therefore importent to
        make sure that your mesh does not have any wholes that you don't want to
        be included."""
        assert not self.trimesh.is_watertight, \
            "This mesh has no holes, so rim cannot be found."
        assert self.trimesh.euler_number == 1, \
            "The mesh has more than one openning so a unique rim cannot be found." \
                f"\n\tEuler number = {self.trimesh.euler_number}" \
                f"\n\tMesh contains {1-self.trimesh.euler_number} holes."
        unique_edges = self.trimesh.edges[tr.grouping.group_rows(self.trimesh.edges_sorted, require_count=1)]

        rim_nodes = {}
        rim_nodes['indices'] = np.unique(unique_edges.flatten())
        rim_nodes['coords'] = self.trimesh.vertices[np.unique(unique_edges.flatten())]

        return rim_nodes
    
    def order_rim_nodes(self) -> dict:
        """
        Makes sure all the points in a polygon are consecutive around the polygon.
        """
        rim_nodes = self.get_boundary_nodes()

        coords = rim_nodes['coords']
        indices = rim_nodes['indices']
        # Creates new coords with same shape as the coords of node positions
        new_coords = np.zeros(shape=np.shape(coords))
        new_indices = np.zeros(shape=np.shape(indices))
        # Sets the first value to the point closest to the y intersept at the maximum x value and mean z value
        new_coords[0] = [np.max(coords[:,0]), np.mean(coords[:,1]), 0] # Changed for aligned with z
        # Finds the distances between the each point in coords and this first value in new_coords
        distances = np.linalg.norm(coords - new_coords[0], axis=1)
        # Fids the index of the minimum distance
        index = np.argmin(distances)
        # Finds the closest point to where the y value goes negative
        n = 2
        if len(new_coords) - len(coords) < 5:
            while coords[index][2] > 0: # Changed from coords[index][2] for when it was aligned with y
                index = np.where(distances == np.partition(distances, n-1)[n-1])[0][0]
                n += 1
            n = 2
        # Sets the closest point as the first point in the new_coords
        new_coords[0] = coords[index]
        new_indices[0] = indices[index]
        coords = np.delete(coords, index, 0) # Deletes this point from the old coords
        indices = np.delete(indices, index, 0)
        i = 1
        # For each point the distance coords is calculated, the index of the
        # minimum distance is found, this is added to the new coords and
        # deleted from the old coords. For the first five terms there is a
        # check to see if we are still going in the negative y direction.
        while coords.any():
            # Calculated distances
            distances = np.linalg.norm(coords - new_coords[i-1], axis=1)
            index = np.argmin(distances) # Find index of min distance
            if len(new_coords) - len(coords) < 5: # Check if we are going in negative y
                while coords[index][2] > 0: # Changed from coords[index][2] for when it was aligned with y
                    index = np.where(distances == np.partition(distances, n-1)[n-1])[0][0]
                    n += 1
                n = 2
            # Set new coords value to the point with the minimum distance.
            new_coords[i] = coords[index]
            new_indices[i] = indices[index]
            # Delete value from old coords
            coords = np.delete(coords, index, 0)
            indices = np.delete(indices, index, 0)
            i += 1
        new_rim_nodes = {}
        new_rim_nodes['indices'] = new_indices
        new_rim_nodes['coords'] = new_coords
        #new_coords = np.delete(new_coords, 0, 0) # Not sure why we did this.
        return new_rim_nodes
    
    def resample_rim_nodes(self, num_nodes):
        """
        Interpolates the points around a polygon.
        """
        rim_nodes = self.order_rim_nodes()
        array = rim_nodes['coords']

        # Cumulative Euclidean distance between successive polygon points.
        # This will be the "x" for interpolation
        d = np.cumsum(np.r_[0, np.sqrt((np.diff(array, axis=0) ** 2).sum(axis=1))])

        # get linearly spaced points along the cumulative Euclidean distance
        d_sampled = np.linspace(0, d.max(), num_nodes)

        # interpolate x and y coordinates
        interp = np.c_[
            np.interp(d_sampled, d, array[:, 0]),
            np.interp(d_sampled, d, array[:, 1]),
            np.interp(d_sampled, d, array[:, 2]),
        ]
        rim_nodes['coords'] = interp
        return rim_nodes


class LinerINPMesh(Mesh):
    """
    Class for reading, getting and editing the array of nodes and then
    saving the editted inp file with those edits.
    """
    def __init__(self, name: str, f_name: str, f_folder: str, description: str=None):
        super().__init__(name=name, f_name=f_name, f_type='inp', f_folder=f_folder, description=description)
        # Set stl path
        self.stl_path = self.path(file_type='stl')

        # Liner dimensions
        self.dimensions = self.get_liner_dimensions()

        # NPY
        self.elements = None
        self.nodes = None

        # INP
        self._inp_head = []        # Heading for the inp file
        self.part_head = []       # Heading for the part
        self.elem_head = []       # Heading for the elements i.e. type
        self._inp_tail = []        # Tail for the inp file

        self.rim_nodes = []
        self.num_rim_nodes = None
        # TODO: Refactor this to not have WDIR here in this form
        self.rim_nodes_path = os.path.join()#WDIR, self.f_folder, 'RimNodes.npy')

        self.read_inp()

    def read_inp(self):
        """Reads data from an ascii encoded inp file to the INPMesh object"""
        data_list = []
        with open(self.f_path, 'r', encoding="utf-8") as file:
            data_list = file.readlines()
        [indexes, instances] = self.find_index(data_list, '*Part,')
        assert len(indexes) == 1, f'Can only process inp files with one part, {len(indexes)} were given.'

        part_index = indexes[0]
        [n_indexes, n_insts] = self.find_index(data_list, '*Node')
        assert len(n_indexes) == 1, f'Can only process inp files with one node section, {len(n_indexes)} are given.'
        node_index = n_indexes[0]

        self._inp_head = data_list[:node_index]
        self.part_head = instances[0].strip()
        self.part_name = instances[0].split('=')[-1].strip()

        [e_indexes, e_insts] = self.find_index(data_list, '*Element')

        elem_index = e_indexes[0]

        self.elem_head = e_insts[0].strip()

        node_list = data_list[node_index + 1: elem_index]

        self.nodes \
            = np.array([[float(item.strip()) for item in line.split(',')] for line in node_list])

        elem_end = self.find_num_elements(elem_index + 1, data_list)

        elem_list = data_list[elem_index + 1: elem_end]

        self.elements \
            = np.array([[int(item.strip()) for item in line.split(',')] for line in elem_list])

        self._inp_tail = data_list[elem_end:]

    def change_units(self, factor):
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = node[1:]*factor

    def find_num_elements(self, starting_index, data_list):
        """Finds the number of elements in the inp file."""
        index = starting_index
        while self._try(data_list[index].split(',')[0]):
            index += 1
        return index

    def _try(self, item):
        try:
            return int(item)
        except:
            return False

    def find_index(self, data_list, keyword_input):
        """Finds the index if a keyword in a file list"""
        wildcard = '*'
        instances = fnm.filter(data_list, keyword_input + wildcard)
        index = []
        if len(instances) > 0:
            for instance in instances:
                index.append(data_list.index(instance))
            return [index, instances]
        else:
            print('No ' + keyword_input + ' found, check the output file for completeness!')
            return

    def write_inp(self, file_name: str):
        """Write the changed inp file."""
        file_name = file_name[:-4] if file_name[-4:] == '.inp' else file_name
        with open(self.path(file_name), 'w', encoding="utf-8") as file:
            for line in self._inp_head:
                file.write(line)
            #file.write(f'{self.part_head}\n')
            file.write('*Node\n')
            for node in self.nodes:
                file.write(f'{int(node[0]):>7},  {node[1]:>11},  {node[2]:>11},  {node[3]:>11}\n')
            file.write(f'{self.elem_head}\n')

            for element in self.elements:
                file.write(f'{element[0]}')
                for item in element[1:]:
                    file.write(f', {item}')
                file.write('\n')
            for line in self._inp_tail:
                file.write(line)

    def write_stl(self):
        """Writes the inp mesh as a stl."""
        if len(self.elements[0]) != 4:
            raise ValueError('You cannot only convert a trimesh to stl')
        with open(self.path(file_type='stl'), 'w', encoding="utf-8") as file:
            file.write(f'solid "{self.part_name}"\n')
            for element in self.elements:
                nodes = self.nodes[[i-1 for i in element[1:]]]
                normals = self.calculate_normals(nodes)
                file.write('  facet normal ' \
                           f'{float(f"{normals[0]:.12g}"):g} ' \
                           f'{float(f"{normals[1]:.12g}"):g} ' \
                           f'{float(f"{normals[2]:.12g}"):g}\n')
                file.write('    outer loop\n')
                for i in range(3):
                    file.write('      vertex')
                    for j in range(3):
                        file.write(f' {nodes[i][j+1]}')
                    file.write('\n')
                file.write('    endloop\n')
                file.write('  endfacet\n')
            file.write(f'endsolid "{self.part_name}"')

    def calculate_normals(self, nodes):
        """Calculates the normals for each face."""
        v1 = nodes[0][1:4] - nodes[1][1:4]
        v2 = nodes[0][1:4] - nodes[2][1:4]
        normal_vector = np.cross(v1, v2)
        magnitude = normal_vector[0]**2 + normal_vector[1]**2 + normal_vector[2]**2
        unit_normal_vector = normal_vector / magnitude
        return unit_normal_vector

    def get_liner_dimensions(self):
        """Reads the Variabls.txt file that create_liner.py creates to store
        the important variables relating to the dimensions and type of mesh
        that we have created in ABAQUS."""
        with open(os.path.join(self.f_folder, 'Dimensions.txt'), encoding="utf-8") as file:
            lines = file.readlines()
        dimensions = {}
        for line in lines:
            dimensions[line.split('=')[0].strip()] = float(line.split('=')[1].strip().split()[0])
        return dimensions

    def get_rim_nodes(self) -> None:
        """Gets the indices and coordinates of the liner rim nodes and the
        number of them saving them in self.rim_nodes and self.num_rim_nodes."""
        # Y value of the rim of the liner
        liner_rim = self.dimensions['Length'] - (self.dimensions['Diameter']/2)

        # Get the indices of the nodes with a y value of liner_rim
        indices = np.transpose(np.argwhere(self.nodes[:,2] == float(liner_rim)))[0]

        # Use the index to get all the nodes with a y value of liner_rim
        self.rim_nodes = self.nodes[indices]

        # Get the number of rim nodes
        self.num_rim_nodes = len(indices)

    def apply_transformation(self, transformation_matrix):
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = np.dot(transformation_matrix,np.append(node[1:],1))[:3]

    def save_rim_nodes(self, file_name: str) -> None:
        """Saves the indices and coordinates of the rim nodes in an npy file."""
        # TODO: Refactor this to not include WDIR here
        file_path = os.path.join()#WDIR, self.f_folder, file_name)
        np.save(file_path, self.rim_nodes)

def cut_meshes(meshes: list[STLMesh],
               offset:float=0.210,
               norm_vect:tuple=(-0.3545, 0.9166, 0.0)) -> list[STLMesh]:
    """
    Cuts all the meshes within the list meshes, of MeshObj objects (meshes)
    and cuts them off acocrding to the offset and norm_vect parameters where
    offset is the distance from the origin and norm_vect is the vector that
    is normal to the cutting plane.
    """
    for i, mesh in enumerate(meshes):
        mesh.cut_mesh(plane_axis=3,
                      plane_offset=offset,
                      section=2,
                      custom_axis=norm_vect)
        meshes[i] = STLMesh('CutMesh', f'{mesh.f_name}_cut', mesh.f_folder)
    return meshes

if __name__ == "__main__":
    pass
