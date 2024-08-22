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
from dataclasses import dataclass

FOLDER = 'Geometry'

@dataclass
class Boundary():
    """ Data class for holding information about the boundary of a mesh. """
    nodes: np.ndarray = None
    nodes_sorted: bool = False
    is_watertight: bool = None
    edges: np.ndarray = None
    edges_sorted: bool = False
    faces: np.ndarray = None
    num_nodes: int = None
    corner_nodes: list = None
    corner_node_angle_threshold: float = None
    interpollation_coords: np.ndarray = None
    interpollation_num: np.ndarray = None


class Mesh():
    """Class for containing all the information common between meshes"""
    def __init__(self, name: str, f_name: str, f_type: str, f_folder: str,
                 description: str='') -> None:
        self.name = name
        self.f_name = f_name
        self.description = description
        self.f_type = f_type
        self.f_folder = f_folder
        self.f_path = self.path()
        self.num_nodes:int = None
        self.num_elements:int = None
        self.boundary: Boundary = Boundary()
        self.units:str = None

        self.nodes: np.ndarray = None

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

    def set_units(self, units: str):
        self.units = units


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
    def __init__(self, name: str, f_name: str, f_folder: str,
                 description: str=None, load: bool=True) -> None:
        Mesh.__init__(self, name, f_name, 'stl', f_folder, description)

        self.trimesh = None

        if load:
            self.load_stl()

        # TODO: Potentially a better idea to not have so many landmark points,
        # but instead have a few, then transform all the rim nodes to the same
        # value.
        # This is specifically for the liner meshes and won't help with the
        # collar meshes.

    def load_stl(self) -> None:
        """Loads STL file as trimesh object."""
        self.trimesh: tr.Trimesh = tr.load_mesh(self.path())
        self.nodes = np.array([[i, vertex[0], vertex[1], vertex[2]] for i, vertex in enumerate(self.trimesh.vertices)])
        self.num_nodes = len(self.trimesh.vertices)
        self.num_elements = len(self.trimesh.faces)
        x1 = np.max(self.trimesh.vertices[:][0])
        x2 = np.min(self.trimesh.vertices[:][0])
        if abs(x1 - x2) > 1:
            self.units = "mm"
        else:
            self.units = "m"

    def update_nodes(self, nodes):
        for i, node in enumerate(nodes):
            for j, coord in enumerate(node):
                self.nodes[i, j+1] = coord
        self.trimesh.vertices = nodes

    def save_mesh(self, file_path):
        self.save_trimesh_as_stl(file_path=file_path)

    def save_trimesh_as_stl(self, name=None, file_path=None) -> None:
        """Saves trimesh object as an STL."""
        if file_path:
            f_path = file_path
        elif name:
            f_path = self.path(name)
        self.trimesh.export(file_obj=f_path, file_type='stl_ascii')
        print(f"File successfully saved as {f_path}")

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

    def get_boundary(self) -> np.ndarray:
        """Take a trimesh object as input and returns the coordinates of all the
        nodes that are on a boundary of the mesh. It is therefore importent to
        make sure that your mesh does not have any holes that you don't want to
        be included."""
        assert not self.trimesh.is_watertight, \
            "This mesh has no holes, so rim cannot be found."
        assert self.trimesh.euler_number == 1, \
            "The mesh has more than one openning so a unique rim cannot be found." \
                f"\n\tEuler number = {self.trimesh.euler_number}" \
                f"\n\tMesh contains {1-self.trimesh.euler_number} holes."
        unique_edges = self.trimesh.edges[
            tr.grouping.group_rows(self.trimesh.edges_sorted, require_count=1)
        ]

        self.boundary.edges = unique_edges
        self.boundary.nodes = np.unique(unique_edges.flatten())
        self.arrange_boundary()
        self.boundary.is_watertight = self.trimesh.is_watertight
        self.boundary.num_nodes = len(self.boundary.nodes)
        self.get_boundary_faces()
        self.get_corners(angle_threshold=140.0)
        return self.boundary.nodes

    def arrange_boundary(self) -> None:
        """ Arranges the boundary edges and nodes. """
        self.arrange_boundary_edges()
        self.arrange_boundary_nodes()

    def arrange_boundary_edges(self) -> np.ndarray:
        """ Edges are stored in a nx2 numpy array. """
        if self.boundary.edges is None:
            self.get_boundary()
        boundary_edges = self.boundary.edges

        unsorted_edges = [[item for item in row] for row in boundary_edges]
        sorted_edges = np.zeros(np.shape(boundary_edges), dtype=np.uint32)

        sorted_edges[0,:] = boundary_edges[0,:]
        del unsorted_edges[0]
        index = 1
        while len(unsorted_edges) > 0:
            for edge in unsorted_edges:
                if sorted_edges[index-1,1] in edge:
                    if edge[1] == sorted_edges[index-1,1]:
                        e = reversed(edge)
                    else:
                        e = edge
                    for i, node_index in enumerate(e):
                        sorted_edges[index, i] = node_index
                    unsorted_edges.remove(edge)
                    index += 1
                    break
        self.boundary.edges = sorted_edges
        self.boundary.edges_sorted = True
        return sorted_edges

    def arrange_boundary_nodes(self) -> np.ndarray:
        """ Arranges the nodes array to match the ordered list of edges. """
        if not self.boundary.edges_sorted:
            self.arrange_boundary_edges()
        sorted_nodes = np.zeros(np.shape(self.boundary.nodes), dtype=np.uint32)
        for i, edge in enumerate(self.boundary.edges):
            sorted_nodes[i] = int(edge[0])
        assert set(sorted_nodes) == set(self.boundary.nodes), "Error in sorting nodes."
        self.boundary.nodes = sorted_nodes
        self.boundary.nodes_sorted = True
        return sorted_nodes

    def get_boundary_faces(self) -> list:
        """ Finds all the faces that have edges along the boundary. """
        if self.boundary.nodes is None:
            self.get_boundary()
        boundary_faces = []
        for i, face in enumerate(self.trimesh.faces):
            for item in face:
                if item in self.boundary.nodes and i not in boundary_faces:
                    boundary_faces.append(i)
        self.boundary.faces = boundary_faces
        return boundary_faces

    def get_corners(self, angle_threshold: float=140.0) -> list:
        """ Finds all the corners of a mesh defined by a certain angle threshold. """
        if not self.boundary.edges_sorted:
            self.get_boundary()

        corners = []
        previous_edge = self.boundary.edges[-1]
        for edge in self.boundary.edges:
            nodes = [previous_edge[0], edge[0], edge[1]]
            nodes_coords = [self.trimesh.vertices[i] for i in nodes]
            angle_rad = self.calculate_angle(nodes_coords)
            if angle_rad <= angle_threshold*np.pi/180.0:
                corners.append(edge[0])
            previous_edge = edge
        self.boundary.corner_nodes = corners
        self.boundary.corner_node_angle_threshold = angle_threshold
        return corners

    def calculate_angle(self, nodes):
        """
        Calculates the angle between three nodes.
        nodes:
            iterable of nodes with coordinates [[x1, y1, z1], [x2, y2, z2], [x3, y3, z3]]
            where the angle 1-2-3 is then found.
        """
        v1 = [a_i - b_i for a_i, b_i in zip(nodes[0], nodes[1])]
        v2 = [a_i - b_i for a_i, b_i in zip(nodes[2], nodes[1])]
        dot = np.dot(v1, v2)
        v1_mag = np.linalg.norm(v1)
        v2_mag = np.linalg.norm(v2)
        angle = np.arccos(dot/(v1_mag*v2_mag))
        return angle

    def restarted_arranged_nodes(self, starting_point: np.ndarray=None,
                                 rotational_axis: np.ndarray=None,
                                 ccw_flag: bool=False) -> np.ndarray:
        """
        Arranges the nodes array such that the point closest to 
        starting_point is the first element and the subsequent nodes go around
        in a clockwise direction about the axis (rotation_axis).
        """
        if not self.boundary.nodes_sorted:
            self.arrange_boundary()
        if not starting_point:
            starting_point = np.array([0.0, 0.0, -1.0])
        if not rotational_axis:
            rotational_axis = np.array([0.0, 1.0, 0.0])
        if ccw_flag:
            rotational_axis = np.copysign(rotational_axis,-1)

        coords = self.trimesh.vertices[self.boundary.nodes]
        indices = self.boundary.nodes
        new_indices = np.zeros(np.shape(indices), dtype=np.uint32)
        # Calculate the distances from the start point to each of the boundary nodes
        distances = np.linalg.norm(coords - starting_point, axis=1)
        # Index of the closest value
        index = np.argmin(distances)
        # Checks to see if the order of the nodes is going round the z axis in
        # a clockwise rotation < 0 or a counter-clockwise rotation > 0
        # direction.
        rotation = np.dot(rotational_axis, np.cross(coords[index], coords[index+1]))
        if rotation > 0:
            indices = np.flip(indices)
            print("Index array has been flipped.")
        for i, item in enumerate(new_indices):
            if i + index < len(indices):
                new_indices[i] = indices[i + index]
            else:
                new_indices[i] = indices[i + index - len(indices)]
        assert set(new_indices) == set(indices), "Rearranging indices has failed"
        return new_indices

    def resample_boundary_nodes(self, num_nodes, ccw_flag: bool=False):
        """
        Interpolates the points around a polygon.
        """
        # TODO: This needs to be redone such that the corner nodes are not
        # affected by the resampling. i.e. between each corner resample, but
        # corners should stay in the same places.
        if self.boundary.nodes is None:
            self.get_boundary()
        if not self.boundary.nodes_sorted:
            self.arrange_boundary()

        boundary_nodes = self.restarted_arranged_nodes(ccw_flag=ccw_flag)
        coords = self.trimesh.vertices[boundary_nodes]
        coords = np.append(coords, [coords[0]], axis=0)

        # Cumulative Euclidean distance between successive polygon points.
        # This will be the "x" for interpolation
        d = np.cumsum(np.r_[0, np.sqrt((np.diff(coords, axis=0) ** 2).sum(axis=1))])
        # get linearly spaced points along the cumulative Euclidean distance
        d_sampled = np.linspace(0, d.max(), num_nodes + 1)

        # interpolate x and y coordinates
        interp_array = np.c_[
            np.interp(d_sampled, d, coords[:, 0]),
            np.interp(d_sampled, d, coords[:, 1]),
            np.interp(d_sampled, d, coords[:, 2]),
        ]
        last_index = len(interp_array) - 1
        interp_array = np.delete(interp_array, last_index, axis=0)

        self.boundary.interpollation_coords = interp_array
        self.boundary.interpollation_num = num_nodes
        return interp_array

    def change_units(self, factor, units):
        """ Changes the units of a mesh by a given factor. """
        self.trimesh.apply_scale(factor)
        self.units = units

    def get_bounding_box(self) -> list:
        """ Gets the xyz values of the centroid, range, maximum and minumum. """
        maximums = [coord for coord in self.trimesh.vertices[0]]
        minimums = [coord for coord in self.trimesh.vertices[0]]
        for node in self.trimesh.vertices:
            for i, coord in enumerate(node[1:]):
                if coord > maximums[i]:
                    maximums[i] = coord
                elif coord < minimums[i]:
                    minimums[i] = coord
        centroid = [ (maximums[i] + minimums[i])/2 for i in range(3)]
        difference = [ maximums[i] - minimums[i] for i in range(3)]
        return centroid, difference, maximums, minimums


class INPMesh(Mesh):
    """
    Class for reading, getting and editing the array of nodes and then
    saving the editted inp file with those edits.
    """
    def __init__(self, name: str, f_name: str, f_folder: str, description: str=None):
        Mesh.__init__(self, name=name, f_name=f_name, f_type='inp',
                      f_folder=f_folder, description=description)
        # Set stl path
        self.stl_path = self.path(file_type='stl')

        # NPY
        self.elements = None
        self.nodes = None

        # INP
        self._inp_head = []        # Heading for the inp file
        self.part_head = []       # Heading for the part
        self.elem_head = []       # Heading for the elements i.e. type
        self._inp_tail = []        # Tail for the inp file

        self.boundary_nodes = []
        self.num_boundary_nodes = None
        self.boundary_nodes_path = None

        self.read_inp()

    def read_inp(self):
        """Reads data from an ascii encoded inp file to the INPMesh object"""
        data_list = []
        with open(self.f_path, 'r', encoding="utf-8") as file:
            data_list = file.readlines()
        try:
            [indexes, instances] = self.find_index(data_list, '*Part,')
            assert len(indexes) == 1, \
                f'Can only process inp files with one part, {len(indexes)} were given.'
            part_index = indexes[0]
            self.part_head = instances[0].strip()
            self.part_name = instances[0].split('=')[-1].strip()
        except:
            print("No *PART found, contining without parts")

        [n_indexes, n_insts] = self.find_index(data_list, '*Node')
        assert len(n_indexes) == 1, \
            f'Can only process inp files with one node section, {len(n_indexes)} are given.'
        node_index = n_indexes[0]

        self._inp_head = data_list[:node_index]

        [e_indexes, e_insts] = self.find_index(data_list, '*Element')

        elem_index = e_indexes[0]

        self.elem_head = e_insts[0].strip()

        node_list = data_list[node_index + 1: elem_index]

        self.nodes \
            = np.array([[float(item.strip()) for item in line.split(',')] for line in node_list])

        [elem_list, elem_end] = self.find_elements(elem_index + 1, data_list)

        self.elements \
            = np.array([[int(item.strip()) for item in line.split(',')] for line in elem_list])

        if len(data_list) == elem_end:
            self._inp_tail = ""
        else:
            self._inp_tail = data_list[elem_end:]

        x1 = np.max(self.nodes[:,1])
        x2 = np.min(self.nodes[:,1])
        if abs(x1 - x2) > 1:
            self.units = "mm"
        else:
            self.units = "m"

    def update_nodes(self, nodes):
        for i, node in enumerate(nodes):
            for j, coord in enumerate(node):
                self.nodes[i,j+1] = coord

    def change_units(self, factor, units):
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = node[1:]*factor
        self.units = units

    def find_elements(self, starting_index, data_list):
        """Finds the number of elements in the inp file. """
        index = starting_index
        elements = []
        more_elements = True
        while more_elements:
            elements.append(data_list[index])
            index += 1
            try:
                int(data_list[index].split(',')[0])
            except:
                return elements, index-1
        return elements, index-1

    def find_index(self, data_list, keyword_input):
        """ Finds the index if a keyword in a file list. """
        wildcard = '*'
        instances = fnm.filter(data_list, keyword_input + wildcard)
        index = []
        if len(instances) > 0:
            for instance in instances:
                index.append(data_list.index(instance))
            return [index, instances]
        else:
            raise ParsingError(keyword_input, "Check that the input file is correctly written.")

    def save_mesh(self, file_path):
        """ Saves the mesh as an inp mesh. """
        self.write_inp(file_path=file_path)

    def write_inp(self, file_name: str=None, file_path: str=None):
        """Write the changed inp file."""
        if file_path:
            f_path = file_path
        elif file_name:
            file_name = file_name[:-4] if file_name[-4:] == '.inp' else file_name
            f_path = self.path(file_name)
        with open(f_path, 'w', encoding="utf-8") as file:
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

    def write_stl(self, file_path:str=None):
        """Writes the inp mesh as a stl."""
        if len(self.elements[0]) != 4:
            raise ValueError('You cannot only convert a trimesh to stl')
        if file_path:
            path = file_path
        else:
            path = self.path(file_type='stl')
        with open(path, 'w', encoding="utf-8") as file:
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

    def get_boundary_nodes(self) -> None:
        """ Gets the indices and coordinates of the liner rim nodes and the
        number of them saving them in self.boundary_nodes and self.num_boundary_nodes. """
        # TODO: Redo this to get all the rim nodes and save in boundary_nodes
        # and num_boundary_nodes. Standardise this which the stl mesh
        # boundary nodes.

    def apply_transformation(self, transformation_matrix):
        """ Applies a given transformation matrix to a mesh. """
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = np.dot(transformation_matrix,np.append(node[1:],1))[:3]

    def save_boundary_nodes(self, file_name: str) -> None:
        """ Saves the indices and coordinates of the rim nodes in an npy file. """
        file_path = os.path.join(self.f_path, self.f_folder, file_name)
        self.boundary_nodes_path = file_path
        np.save(file_path, self.boundary_nodes)

    def get_bounding_box(self) -> list:
        """ Somewhat redundent seeing as I have the units check in the load mesh. """
        maximums = [coord for coord in self.nodes[0, 1:]]
        minimums = [coord for coord in self.nodes[0, 1:]]
        for node in self.nodes:
            for i, coord in enumerate(node[1:]):
                if coord > maximums[i]:
                    maximums[i] = coord
                elif coord < minimums[i]:
                    minimums[i] = coord
        centroid = [ (maximums[i] + minimums[i])/2 for i in range(3)]
        difference = [ maximums[i] - minimums[i] for i in range(3)]
        return centroid, difference, maximums, minimums


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

class ParsingError(Exception):
    """Errer message for reading data from inp or stl files."""
    def __init__(self, keyword, message=None):
        self.message = \
            f"File parsing has failed keyword not found.\n\n{keyword} was not found in the file.\n"
        if message:
            self.message += f"\n{message}\n"
        super().__init__(self.message)


if __name__ == "__main__":
    pass
