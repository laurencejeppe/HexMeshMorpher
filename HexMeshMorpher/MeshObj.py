# -*- coding: utf-8 -*-
"""
Created on Wed Mar 06 12:31:00 2024

@author: ljr1e21
"""

import os
import fnmatch as fnm
import numpy as np
import trimesh as tr
from dataclasses import dataclass
from abc import ABC, abstractmethod

FOLDER = 'Geometry'


@dataclass
class Boundary():
    """ Data class for holding information about the boundary of a mesh. """
    nodes: np.ndarray = None
    nodes_sorted: bool = False
    #is_watertight: bool = None
    #edges: np.ndarray = None
    #edges_sorted: bool = False
    #faces: np.ndarray = None
    num_nodes: int = None
    corner_nodes: list = None
    corner_node_angle_threshold: float = None
    interpollation_coords: np.ndarray = None
    interpollation_num: np.ndarray = None


class Mesh(ABC):
    """Class for containing all the information common between meshes"""

    def __init__(self, name: str, f_name: str, f_type: str, f_folder: str,
                 description: str = '') -> None:
        self.name = name
        self.f_name = f_name
        self.description = description
        self.f_type = f_type
        self.f_folder = f_folder
        self.f_path = self.path()
        self.num_nodes: int = None
        self.num_elements: int = None
        self.boundaries: list = []
        self.units: str = None
        self.unit_factor = 1.0

        self.nodes: np.ndarray = None

    def path(self, file_name: str = None, file_type: str = None):
        """
        Generates the path of the mesh object depending on the f_name and
        f_type.
        """
        f_name = file_name if file_name else self.f_name
        f_type = file_type if file_type else self.f_type
        return os.path.join(self.f_folder, f_name + '.' + f_type)

    def rename(self, file_name: str, file_folder: str = None):
        """Renames the mesh and updates self.f_path."""
        self.f_name = file_name
        self.f_folder = file_folder if file_folder else self.f_folder
        self.f_path = self.path()

    def set_units(self, units: str):
        """
        Changes the string describing the units.
        Changes the unit_factor which determines scaling on various aspects including:
         - the position of the start point used to define automatic landmark detection.
         - can also be used to define view port detection
         - can be used to name files with the units"""
        self.units = units
        if self.units == 'mm':
            self.unit_factor = 1000.0
        elif self.units == 'm':
            self.unit_factor = 1.0
        else:
            self.unit_factor = 1.0

    @abstractmethod
    def load_mesh(self) -> None:
        raise NotImplementedError
    
    def change_units(self, factor, units: str) -> None:
        self.scale_mesh(factor)
        self.set_units(units)

    @abstractmethod
    def scale_mesh(self, factor) -> None:
        raise NotImplementedError
    
    @staticmethod
    def resample_nodes(coords, num_nodes) -> np.ndarray:
        """
        Returns a numpy array of num_nodes coordinates that are evenly
        spaced along the path that is created by successively traversing
        the list of coordinates in coords.
        The first and last coordinates of coords remain in the same place
        and are included in the returned array.
        coords is the array of coordinates of the nodes being resampled.
        num_interp is the number of points you want for the interpolation.
        """
        # Cumulative Euclidean distance between successive polygon points.
        # This will be the "x" for interpolation
        d = np.cumsum(
            np.r_[0, np.sqrt((np.diff(coords, axis=0) ** 2).sum(axis=1))]
            )

        # get linearly spaced points along the cumulative Euclidean distance
        d_sampled = np.linspace(0, d.max(), num_nodes)

        # interpolate x and y coordinates
        interp_array = np.c_[
            np.interp(d_sampled, d, coords[:, 0]),
            np.interp(d_sampled, d, coords[:, 1]),
            np.interp(d_sampled, d, coords[:, 2]),
        ]

        return interp_array
    
    @staticmethod
    def evaluate_corners(coords, angle_threshold: float = 130.0) -> np.ndarray:
        """
        Finds all the corners of a mesh defined by a certain angle threshold.
        Returns a numpy array of the coordinates of the corner nodes.
        Inputs:
            coords: np.ndarray
                An array of coordinates representing a boundary of nodes.
                This should have the same node as the first and last item to represent a closed loop
        Returns:
            corners: np.ndarray
                An array of coordinates thar represent the corners of the mesh.
        """
        assert coords[0].all() == coords[-1].all(), ("The first and last elements of coords are not the same, \
                                         this is not a closed boundary!")
        corners = []
        previous_node = coords[-2]
        for i, current_node in enumerate(coords[:-1]):
            next_node = coords[i + 1]
            nodes_coords = [previous_node, current_node, next_node]
            angle_rad = Mesh.calculate_angle(nodes_coords)
            if angle_rad <= angle_threshold*np.pi/180.0:
                corners.append(current_node)
            previous_node = current_node
        return np.array(corners)
    
    @staticmethod
    def calculate_angle(nodes):
        """
        Calculates the angle between three nodes.
        nodes:
            iterable of nodes with coordinates [[x1, y1, z1],
                                                [x2, y2, z2],
                                                [x3, y3, z3]]
            where the angle 1-2-3 is then found.
        """
        v1 = [a_i - b_i for a_i, b_i in zip(nodes[0], nodes[1])]
        v2 = [a_i - b_i for a_i, b_i in zip(nodes[2], nodes[1])]
        dot = np.dot(v1, v2)
        v1_mag = np.linalg.norm(v1)
        v2_mag = np.linalg.norm(v2)
        angle = np.arccos(dot/(v1_mag*v2_mag))
        return angle


# If you want rotation matrices use
# trimesh.transformations.rotation_matrix(angle, direction, point=None)

# If you want a translation matrix use
# trimesh.transformations.scale_and_translate(scale=None, translate=None)


class TriMesh(Mesh):
    """Class for defining file names and locations where they are saved"""

    def __init__(
            self,
            name: str,
            f_name: str,
            f_folder: str,
            f_type: str='stl',
            description: str = None,
            load: bool = True
        ) -> None:
        super().__init__(
            name=name,
            f_name=f_name,
            f_type=f_type,
            f_folder=f_folder,
            description=description
        )

        self.trimesh = None

        if load:
            self.load_mesh()

    def load_mesh(self):
        self.load_stl()

    def load_stl(self) -> None:
        """Loads STL file as trimesh object."""
        self.trimesh: tr.Trimesh = tr.load_mesh(self.path())
        self.nodes = np.array(
            [[i, vertex[0], vertex[1], vertex[2]]
             for i, vertex in enumerate(self.trimesh.vertices)]
            )
        self.num_nodes = len(self.trimesh.vertices)
        self.num_elements = len(self.trimesh.faces)
        x1 = np.max(self.trimesh.vertices[:][0])
        x2 = np.min(self.trimesh.vertices[:][0])
        # Not very good way of doing this assumes meters if the mesh is smaller than one in its width in the x axis and otherwise assumes millimeters
        if abs(x1 - x2) > 1:
            self.set_units("mm")
        else:
            self.set_units("m")

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
        """
        A function that saves a trimeshe's vertices and faces in npy files.
        This was implemented before the STL saving feature. It may still be
        useful in some instances, so it will be left here.
        """
        vertices = self.trimesh.vertices
        faces = self.trimesh.faces
        np.save("vert_" + self.f_name, vertices)
        np.save("faces_" + self.f_name, faces)

    def load_trimesh_from_npy(self) -> None:
        """
        A function to load trimeshes meshes that have been saved as npy files.
        """
        print("LOADING: " + self.f_name)
        loaded_vertices = np.load("vert_" + self.f_name)
        loaded_faces = np.load("faces_" + self.f_name)
        self.trimesh = tr.Trimesh(loaded_vertices, loaded_faces)
        print("LOADED: " + self.f_name)

    def apply_transformation(self, t_matrix) -> None:
        """Apply transformation matrix to the trimesh object"""
        self.trimesh.apply_transform(t_matrix)

    def copy_mesh(self, new_name: str, new_f_name: str,
                  new_description: str = None):
        """Returns a new STMesh object with the same trimesh"""
        mesh = TriMesh(new_name, new_f_name, self.f_folder, new_description,
                       load=False)
        mesh.trimesh = self.trimesh.copy()
        return mesh

    def get_boundary_nodes(self):
        """Returns a list of node indices for each boundary."""
        boundary_nodes = []
        for boundary in self.boundaries:
            boundary_nodes.append(boundary.nodes[:-1])
        return boundary_nodes

    def get_boundary_coords(self):
        """Returns a list of coordinates for each boundary."""
        boundary_coords = []
        corner_coords = []
        for boundary in self.boundaries:
            boundary_coords.append(self.trimesh.vertices[boundary.nodes[:-1]])
            corner_coords.append([])
        return boundary_coords, corner_coords

    def evaluate_boundary(self,
                          evaluate_corners: bool = False,
                          corner_threshold: float = 130.0) -> np.ndarray:
        """
        Take a trimesh object as input and returns the coordinates of all the
        nodes that are on a boundary of the mesh. It is therefore importent to
        make sure that your mesh does not have any holes that you don't want to
        be included.
        input: 
            evaluate_corners: bool = False
                This flag determines whether or not the corners of the mesh are evaluated.
            corner_threshold: float = 130.0
                This is the angle threshold that determines whether or not a node is considered
                a corner.
        """
        assert not self.trimesh.is_watertight, (
            "This mesh has no holes, so rim cannot be found."
            )
        #assert self.trimesh.euler_number == 1, (
        #    "The mesh has more than one openning so a unique rim cannot be"
        #    f"found.\n\tEuler number = {self.trimesh.euler_number}"
        #    f"\n\tMesh contains {1-self.trimesh.euler_number} holes."
        #    )

        ordered_node_array = self.get_ordered_node_array()

        for i, node_array in enumerate(ordered_node_array):
            boundary = Boundary()
            boundary.nodes = node_array
            self.boundaries.append(boundary)

            # Evaluate corners should not be linked into this evaluate boundary
            evaluate_corners = False
            if evaluate_corners:
                corner_node_coords = (
                    self.evaluate_corners(coords=self.trimesh.vertices[node_array],
                                                        angle_threshold=corner_threshold)
                )

        return self.boundaries
        #(self.trimesh.vertices[ordered_node_array], corner_node_coords if evaluate_corners else None)

    def get_ordered_node_array(self):
        # Determine the unique edges of the mesh.
        # These are the edges that are only used by one face of the mesh.
        # These edges are the boundary edges of the mesh.
        unique_edges = self.trimesh.edges[
            tr.grouping.group_rows(self.trimesh.edges_sorted, require_count=1)
        ]

        # Determine the unique nodes of the mesh that are on the boundary.
        unique_nodes = np.unique(unique_edges.flatten())

        # Arranging the boundary edges and nodes to be in order around the rim of the mesh.
        boundary_path_kwargs = tr.path.exchange.misc.edges_to_path(unique_edges,
                                                                   self.trimesh.vertices)

        boundary_path = tr.path.Path3D(**boundary_path_kwargs)
        # All this does is convert the dict to path object

        num_boundaries = len(boundary_path.entities)
        boundary_entities = boundary_path.entities

        boundary_line_entity = boundary_path.entities[0]

        # This ordered_nodes array contains the nodes that are on the boundary of the mesh in order.
        # This is important for the resampling of the boundary nodes to be done correctly.
        # The first and last nodes in the ordered_nodes array are the same node,
        # so the array is closed.
        ordered_nodes_list = []
        for boundary_entity in boundary_entities:
            ordered_nodes = np.array(boundary_entity.to_dict()['points'])
            boundary_points = boundary_entity.points # List of indices
            boundary_edges = boundary_entity.nodes # List of pairs of indices
            boundary_coords = boundary_path.discrete # These are the coords of the nodes around the path

            if boundary_line_entity.closed:
                print("Boundary is closed, making a complete circle")

            # Changing the starting node of the ordered list of nodes
            instersect, intersecting_edge = self.find_intersecting_edge(boundary_edges)
            intersecting_edge_coords = self.trimesh.vertices[intersecting_edge]

            # TODO: This is hard coding and should not be maintained like this
            #print(intersecting_edge_coords)
            if intersecting_edge_coords[0][2] >= 0.0:
                start_node = intersecting_edge[0]
            else:
                start_node = intersecting_edge[0]

            restarted_node_list = self.change_node_list_start(ordered_nodes[:-1], start_node)
            restarted_node_list = np.append(restarted_node_list, restarted_node_list[0])

            # Flipping the orientation of the list if it does not align with rotational axis
            rotational_axis: np.ndarray = np.array([0.0, 1.0, 0.0])
            coords = self.trimesh.vertices[restarted_node_list]
            rotation = self.check_path_rotation_axis(coords)
            if np.dot(rotation, rotational_axis) < 0:
                # Rotation is left-handed about rotational_axis
                restarted_node_list = np.flip(restarted_node_list)
                print("Index array has been flipped to ensure right-handed rotation.")

            ordered_nodes_list.append(restarted_node_list)

        if set([x for sublist in ordered_nodes_list for x in sublist]) == set(unique_nodes):
            print("Boundary nodes are the same as the boundary path points")
        else:
            print("Boundary nodes are NOT the same as the boundary path points")

        return ordered_nodes_list

    def restarted_arranged_nodes(self, starting_point: np.ndarray,
                                 rotational_axis: np.ndarray = np.array([0.0, 1.0, 0.0])
                                 ) -> np.ndarray:
        """
        Arranges the nodes array such that the point closest to
        starting_point is the first element and the subsequent nodes go around
        in a clockwise direction about the axis (rotation_axis).
        """
        coords = self.trimesh.vertices[self.boundary.nodes]
        nodes = self.boundary.nodes

        # Get the starting point
        if self.boundary.corner_nodes:
            corner_coords = self.trimesh.vertices[self.boundary.corner_nodes]
            corner_nodes = self.boundary.corner_nodes
            node_num = self.get_closest_node(corner_coords, corner_nodes, starting_point)
        else:
            # TODO: If you want to make this a point on the yz-plane you should
            #  - find the nodes with the smallest magnitude negative and positive
            #       z values that also have positive x value

            node_num = self.get_closest_node(coords, nodes, starting_point)


        # Split and rejoin the array
        new_node_list = self.change_node_list_start(nodes, node_num)

        # Checks to see if the order of the nodes is going round the y axis in
        # a clockwise rotation < 0 or a counter-clockwise rotation > 0
        # direction.
        coords = self.trimesh.vertices[new_node_list]
        rotation = self.check_path_rotation_axis(coords)
        if np.dot(rotation, rotational_axis) < 0:
            # Rotation is left-handed about rotational_axis
            new_node_list = np.flip(new_node_list)
            print("Index array has been flipped to ensure right-handed rotation.")

        return new_node_list

    def get_closest_node(self, coords: np.ndarray, nodes:np.ndarray, starting_point):
        """
        Calculate the distance from the coords to the starting point and return the
        corresponding node.
        """
        distances = np.linalg.norm(coords - starting_point, axis=1)
        closest_node = nodes[np.argmin(distances)]
        return closest_node

    def change_node_list_start(self, node_list: np.ndarray, start_node: int):
        index = np.where(node_list == start_node)[0][0]
        [a1, a2] = np.split(node_list, np.array([index]))
        new_node_list = np.concatenate((a2, a1, ))
        assert set(new_node_list) == set(node_list), (
            "Rearranging indices has failed"
        )
        return new_node_list

    def change_coord_list_start(self, coord_list: np.ndarray, index: int):
        [a1, a2] = np.split(coord_list, np.array([index]))
        return np.concatenate((a1, a2, ))

    def find_the_point_of_intersection_with_xy_plane(self, coords: np.ndarray):
        """
        This will be a temporary hard coded option for defining where you want
        the start of the node array to be.
        Will find the point at which the array of coords crosses the xy-plane.
        (i.e. when z is zero)
        """
        # Find the consecutive node coords where the sign of z changes
        intersect_points = None
        index = 0
        for coord_1, coord_2 in zip(coords[:-1], coords[1:]):
            if coord_1[2]*coord_2[2] < 0 and coord_1[0] > 0:
                intersect_points = [coord_1, coord_2]
                break
            index += 1

        if intersect_points is None:
            return None

        point_1 = intersect_points[0]
        point_2 = intersect_points[1]

        # Find the linear interpolation of these two points that intersects the xy-plane
        z = 0.0
        x = point_1[0] + (z - point_1[2])*(point_2[0] - point_1[0])/(point_2[2] - point_1[2])
        y = point_1[1] + (z - point_1[2])*(point_2[1] - point_1[1])/(point_2[2] - point_1[2])
        intersection = np.array([x, y, z])
 
        # This will need to be coupled with findng the node indices 
        # as well as defining a new start point for the node array based on this.
        return intersection, intersect_points
    
    def find_intersecting_edge(self, edges):
        intersecting_edge = None
        edge_sections = []
        for edge in edges:
            coords = self.trimesh.vertices[edge]
            if coords[0][0] < 0:
                continue
            [is_intersect, intersect] = self.is_intersection(coords[0], coords[1])
            if is_intersect:
                intersecting_edge = edge
        return intersect, intersecting_edge

    def is_intersection(self, point_1, point_2, plane_point=[0.0, 0.0, 0.0],
        plane_normal=[0.0, 0.0, 1.0]):

        p1 = np.array(point_1)
        p2 = np.array(point_2)
        p_point = np.array(plane_point)
        p_normal = np.array(plane_normal)

        v = p2 - p1
        dot_v_n = np.dot(v, p_normal)

        if np.isclose(dot_v_n, 0.0):
            if np.isclose(np.dot(p1 - p_point, p_normal), 0.0):
                return True, p1
            return False, None

        t = np.dot(p_point - p1, p_normal) / dot_v_n

        if 0.0 <= t <= 1.0:
            intersection_point = p1 + t * v
            return True, intersection_point

        return False, None

    def check_path_rotation_axis(self, coords):
        normalised_coords = coords / np.linalg.norm(coords, axis=1)[:, None]
        axes = np.cross(normalised_coords[:-1], normalised_coords[1:])
        axis = axes.mean(axis=0)
        axis /= np.linalg.norm(axis)
        return axis

    def resample_boundary_nodes(self, num_nodes, ccw_flag: bool = False,
                                ignore_corners: bool = False):
        """
        Interpolates the points around a polygon.
        """
        boundary_index = 0
        # TODO: make so that this resampling does the resampling across all the boundaries.
        assert self.boundaries[boundary_index].nodes is not None, ("No boundary nodes are present")
        if not self.boundaries[boundary_index].nodes_sorted:
            print("Warning! The boundary_nodes_sorted flag suggests the nodes are not sorted.")

        boundary_nodes = self.boundaries[boundary_index].nodes[:-1]
        coords = self.trimesh.vertices[boundary_nodes]

        is_intersection, intersect = self.is_intersection(coords[0], coords[-1])
        if is_intersection:
            coords = np.vstack([intersect, coords, intersect])

        if self.boundaries[boundary_index].corner_nodes and not ignore_corners:
            # TODO: Adjust the nodes number to be representitive of the total
            # number of nodes.
            sub_num_nodes = int(num_nodes/len(self.boundaries[boundary_index].corner_nodes))
            indexes = []
            for i, boundary_node in enumerate(boundary_nodes):
                if boundary_node in self.boundaries[boundary_index].corner_nodes:
                    indexes.append(i)
            indexes.insert(0, 0)
            indexes.append(-2)
            coords_list = []
            for i in range(len(self.boundaries[boundary_index].corner_nodes) + 1):
                limit = [indexes[i], indexes[i+1]]
                coords_list.append(
                    self.trimesh.vertices[boundary_nodes[limit[0]:limit[1]+1]]
                    )
            coords_list[-1] = np.append(coords_list[-1],
                                        coords_list[0],
                                        axis=0)
            del coords_list[0]
            interp_array = np.array([[None, None, None]])
            for coords in coords_list:
                resampled_points = self.resample_nodes(coords,
                                                       sub_num_nodes + 1)
                last_index = len(resampled_points) - 1
                resampled_points = np.delete(resampled_points, last_index, 0)
                interp_array = np.concatenate(
                    (interp_array, resampled_points,),
                    axis=0
                    )

        else:
            # You can do this with a trimesh path object trimesh.path.traversal.resample_path()
            # Might want to keep it as is so that I can use the resampling with a non-trimesh object

            interp_array = self.resample_nodes(coords, num_nodes + 1)

        self.boundaries[boundary_index].interpollation_coords = interp_array[:-1]
        # You should only do this if your edge is very close to the value your a fixing it as.
        self.boundaries[boundary_index].interpollation_coords[:,1] = 360 # This offsets all the landmark coords at the boundary to a specific value. It assumes this is in the zx-plane so fixes y values.
        self.boundaries[boundary_index].interpollation_num = num_nodes
        return self.boundaries[boundary_index].interpollation_coords

    def scale_mesh(self, factor):
        """ Scales the mesh by a given factor. """
        self.trimesh.apply_scale(factor)

    def get_bounding_box(self) -> list:
        """
        Gets the xyz values of the centroid, range, maximum and minumum.
        """
        maximums = [coord for coord in self.trimesh.vertices[0]]
        minimums = [coord for coord in self.trimesh.vertices[0]]
        for node in self.trimesh.vertices:
            for i, coord in enumerate(node[1:]):
                if coord > maximums[i]:
                    maximums[i] = coord
                elif coord < minimums[i]:
                    minimums[i] = coord
        centroid = [(maximums[i] + minimums[i])/2 for i in range(3)]
        difference = [maximums[i] - minimums[i] for i in range(3)]
        return centroid, difference, maximums, minimums


class INPMesh(Mesh):
    """
    Class for reading, getting and editing the array of nodes and then
    saving the editted inp file with those edits.
    """

    def __init__(
            self,
            name: str,
            f_name: str,
            f_folder: str,
            description: str = None
        ) -> None:
        super().__init__(
            name=name,
            f_name=f_name,
            f_type='inp',
            f_folder=f_folder,
            description=description
        )
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

        self.load_mesh()

    def load_mesh(self):
        self.read_inp()

    def read_inp(self):
        """ Reads data from an ascii encoded inp file to the INPMesh object."""
        data_list = []
        with open(self.f_path, 'r', encoding="utf-8") as file:
            data_list = file.readlines()
        try:
            [indexes, instances] = self.find_index(data_list, '*Part,')
            assert len(indexes) == 1, (
                f"Can only process inp files with one part, {len(indexes)} "
                "were given."
                )
            part_index = indexes[0]
            self.part_head = instances[0].strip()
            self.part_name = instances[0].split('=')[-1].strip()
        except:
            print("No *PART found, contining without parts")

        [n_indexes, n_insts] = self.find_index(data_list, '*Node')
        assert len(n_indexes) == 1, (
            "Can only process inp files with one node section, "
            f"{len(n_indexes)} are given."
            )
        node_index = n_indexes[0]

        self._inp_head = data_list[:node_index]

        [e_indexes, e_insts] = self.find_index(data_list, '*Element')

        elem_index = e_indexes[0]

        self.elem_head = e_insts[0].strip()

        node_list = data_list[node_index + 1: elem_index]

        self.nodes = (
            np.array([[float(item.strip()) for item in line.split(',')]
                      for line in node_list])
            )

        [elem_list, elem_end] = self.find_elements(elem_index + 1, data_list)

        self.elements = (
            np.array([[int(item.strip()) for item in line.split(',')]
                      for line in elem_list])
            )

        if len(data_list) == elem_end:
            self._inp_tail = ""
        else:
            self._inp_tail = data_list[elem_end:]

        x1 = np.max(self.nodes[:, 1])
        x2 = np.min(self.nodes[:, 1])
        # Not very good way of doing this assumes meters if the mesh is smaller than one in its width in the x axis and otherwise assumes millimeters
        if abs(x1 - x2) > 1:
            self.set_units("mm")
        else:
            self.set_units("m")

    def update_nodes(self, nodes):
        for i, node in enumerate(nodes):
            for j, coord in enumerate(node):
                self.nodes[i, j+1] = coord

    def scale_mesh(self, factor):
        """ Scales the mesh by a given factor.
        Mostly used to change the units.
        """
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = node[1:]*factor

    def find_elements(self, starting_index, data_list):
        """Finds the number of elements in the inp file. """
        index = starting_index
        elements = []
        more_elements = True
        skip = 0
        while more_elements:
            # The following combines lines that have been split in the inp file due to the 16 item limit. It checks if the line ends with a comma, if it does it combines
            if data_list[index].strip().endswith(','):
                data_list[index] = data_list[index].strip() + data_list[index+1].strip()
                skip = 1
            else:
                skip = 0
            elements.append(data_list[index])
            index += 1 + skip
            try:
                int(data_list[index].split(',')[0])
            except:
                return elements, index-1-skip
        return elements, index-1-skip

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
            raise ParsingError(keyword_input, (
                "Check that the input file is correctly written."
                ))

    def save_mesh(self, file_path):
        """ Saves the mesh as an inp mesh. """
        self.write_inp(file_path=file_path)

    def write_inp(self, file_name: str = None, file_path: str = None):
        """Write the changed inp file."""
        if file_path:
            f_path = file_path
        elif file_name:
            file_name = (
                file_name[:-4] if file_name[-4:] == '.inp' else file_name
                )
            f_path = self.path(file_name)
        with open(f_path, 'w', encoding="utf-8") as file:
            for line in self._inp_head:
                file.write(line)
            # file.write(f'{self.part_head}\n')
            file.write('*Node\n')
            for node in self.nodes:
                file.write(
                    f"{int(node[0]):>7},  {node[1]:>11},  {node[2]:>11},  "
                    f"{node[3]:>11}\n"
                    )
            file.write(f'{self.elem_head}\n')

            for element in self.elements:
                file.write(f'{element[0]}')
                for item in element[1:]:
                    file.write(f', {item}')
                file.write('\n')
            for line in self._inp_tail:
                file.write(line)

    def write_stl(self, file_path: str = None):
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
                file.write('  facet normal '
                           f'{float(f"{normals[0]:.12g}"):g} '
                           f'{float(f"{normals[1]:.12g}"):g} '
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
        magnitude = (
            normal_vector[0]**2 + normal_vector[1]**2 + normal_vector[2]**2
            )
        unit_normal_vector = normal_vector / magnitude
        return unit_normal_vector

    def get_boundary_nodes(self) -> None:
        """
        Gets the indices and coordinates of the liner rim nodes and the
        number of them saving them in self.boundary_nodes and
        self.num_boundary_nodes.
        """
        # TODO: Redo this to get all the rim nodes and save in boundary_nodes
        # and num_boundary_nodes. Standardise this which the stl mesh
        # boundary nodes.

    def apply_transformation(self, transformation_matrix):
        """ Applies a given transformation matrix to a mesh. """
        for i, node in enumerate(self.nodes):
            self.nodes[i][1:] = np.dot(
                transformation_matrix, np.append(node[1:], 1)
                )[:3]

    def save_boundary_nodes(self, file_name: str) -> None:
        """
        Saves the indices and coordinates of the rim nodes in an npy file.
        """
        file_path = os.path.join(self.f_path, self.f_folder, file_name)
        self.boundary_nodes_path = file_path
        np.save(file_path, self.boundary_nodes)

    def get_bounding_box(self) -> list:
        """
        Somewhat redundent seeing as I have the units check in the load mesh.
        """
        maximums = [coord for coord in self.nodes[0, 1:]]
        minimums = [coord for coord in self.nodes[0, 1:]]
        for node in self.nodes:
            for i, coord in enumerate(node[1:]):
                if coord > maximums[i]:
                    maximums[i] = coord
                elif coord < minimums[i]:
                    minimums[i] = coord
        centroid = [(maximums[i] + minimums[i])/2 for i in range(3)]
        difference = [maximums[i] - minimums[i] for i in range(3)]
        return centroid, difference, maximums, minimums


class ParsingError(Exception):
    """Errer message for reading data from inp or stl files."""

    def __init__(self, keyword, message=None):
        self.message = (
            f"File parsing has failed keyword not found.\n\n{keyword} was not "
            "found in the file.\n"
            )
        if message:
            self.message += f"\n{message}\n"
        super().__init__(self.message)


if __name__ == "__main__":
    pass
