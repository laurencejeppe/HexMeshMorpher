"""
Performs amberg non-rigid ICP on the trimesh objects of source and target
objects are returns to the mapping in the mapped object which is returned.
"""

import time
import trimesh as tr
import MeshObj

class AmbergMapping:
    """
    Performs amberg non-rigid ICP on the trimesh objects of source and target
    objects and returns to the mapping in the mapped object which is
    returned.
    """
    def __init__(self, sourcey: MeshObj.STLMesh, targety: MeshObj.STLMesh,
                 mappedy: MeshObj.STLMesh, lpairs: list=None,
                 steps: list=None, options=None) -> None:
        self.source = sourcey
        self.target = targety
        self.mapped = mappedy
        self.gamma = 1
        self.epsilon = 0.001
        self.neighbors_count = 8
        self.distance_threshold = 0.1
        self.use_faces = False # Changing to True causes error (installed rtree with pip to solve)
        self.use_landmarks = False
        ops = {
            'gamma':self.gamma,
            'epsilon':self.epsilon,
            'neighbors':self.neighbors_count,
            'distance_threshold':self.distance_threshold,
            'use_faces':self.use_faces,
            'use_landmarks':self.use_landmarks,
        }
        print(options)
        if options:
            for item in ops:
                if item in options: ops[item] = options[item]
        
        if steps:
            self.steps = steps
        else:
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
        if self.use_landmarks:
            source_indices = [pair[0] for pair in self.landmark_pairs]
            target_points = [pair[1] for pair in self.landmark_pairs]

            start_time = time.time()
            print("Performing Amberg Mapping")
            morphed_vertices \
                = tr.registration.nricp_amberg(self.source.trimesh,
                                                self.target.trimesh,
                                                use_faces=self.use_faces,
                                                source_landmarks=source_indices,
                                                target_positions=target_points,
                                                steps=self.steps,
                                                gamma=self.gamma,
                                                eps=self.epsilon,
                                                neighbors_count=self.neighbors_count,
                                                distance_threshold=self.distance_threshold)
            self.mapped.trimesh = tr.Trimesh(vertices=morphed_vertices,
                                                faces=self.source.trimesh.faces)
            print("Amberg Mapping Completed in " + str(time.time() - start_time) + "s")
        else:
            start_time = time.time()
            print("Performing Amberg Mapping")
            morphed_vertices = tr.registration.nricp_amberg(self.source.trimesh,
                                                            self.target.trimesh,
                                                            use_faces=self.use_faces,
                                                            steps=self.steps,
                                                            gamma=self.gamma,
                                                            eps=self.epsilon,
                                                            neighbors_count=self.neighbors_count,
                                                            distance_threshold=self.distance_threshold)
            self.mapped.trimesh = tr.Trimesh(vertices=morphed_vertices,
                                             faces=self.source.trimesh.faces)
            print("Amberg Mapping Completed in "+str(time.time()-start_time)+"s")

    def find_vertex_index(self, mesh: MeshObj.STLMesh, vertex):
        """Finds the index of a vertex in the mesh [mesh_name] given its position."""
        for i, mesh_vertex in enumerate(mesh.trimesh.vertices):
            if (mesh_vertex == vertex).all():
                return i
