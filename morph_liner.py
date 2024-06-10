"""
This code runs the mesh morphing algorithm for the liner mesh to morph it onto
the surface of the residual limb.

The mesh morphing process first does a non-rigid ICP using the Ambergs method
to adapt the liner mesh to the residuum shape.

Following this a radial bias function is used to generate the necessary
transformation matrix to allow for the whole 3D mesh to be transformed to the
desired position around the residuum
"""
import sys
import os

WDIR = 'D:/ljr1e21/Documents/TIDAL Network+ Project/'
os.chdir(WDIR)

sys.path.append(os.path.join(WDIR, 'Code'))

import MeshObj
import MeshMorphPy_ljr as MeshMorph
from RBFMorph import RBFMorpher

FOLDER = 'Liner Model'
LINER_RIM_Y = 200.0

def load_liner_surface(from_inp: bool=True) -> MeshObj.STLMesh:
    """This convertes the liner inp file to an stl saves it and returns it
    as an MeshObj.STLMesh object"""
    if from_inp:
        # Load liner surface inp file
        liner_surface_inp = MeshObj.LinerINPMesh('Liner Surface Mesh',
                                                 'LinerSurface',
                                                 os.path.join(WDIR, 'Liner Model'),
                                                 description='Unmorphed liner inp surface mesh')
        liner_surface_inp.write_stl()   # Save as stl

    # Load liner surface stl file
    liner_s = MeshObj.STLMesh('Liner Surface Mesh', 'LinerSurface',
                              os.path.join(WDIR, 'Liner Model'),
                              description='Unmorphed liner surface mesh')
    return liner_s


def amberg_map_liner(source: MeshObj.STLMesh, target: MeshObj.STLMesh, output_name: str=None, lpairs: list=None):
    """Creates a mesh mapped to the surface of the skin (target) mesh with
    correspondence to the liner surface (source) mesh."""
    name = output_name if output_name else 'LinerSurfaceMorphed'
    output = MeshObj.STLMesh('Mapped Liner Surface Mesh',
                             name,
                             f_folder=os.path.join(WDIR, FOLDER),
                             load=False)

    # Steps defines the weightings for each of the components in the cost
    # funtion. By default there are 4 outer loop steps between which these
    # weightings are varied. For each of these the weightings are defined.
    # The first is the weighting for the stiffness of the deformations.
    # The higher this is the less deformation will occur more like a rigid icp.
    # The second is the weighting for the landmark points if they are used.
    # This should be set to a high value to make sure the landmarks are kept
    # exactly in place.
    # The thrid is the overall displacement of the points. But setting this
    # high seems only to prevent the mesh from getting a good match to the
    # surface.
    # The final value is the maximum number of iterations for that inner loop.
    # The default values are:
    default = [
        [0.01, 10, 0.5, 10],
        [0.02, 5, 0.5, 10],
        [0.03, 2.5, 0.5, 10],
        [0.01, 0, 0.0, 10],
    ]
    # Default values with the addition of being strick with landmarks
    landmarks = [
        [0.01, 10, 0.5, 10],
        [0.02, 10, 0.5, 10],
        [0.03, 10, 0.5, 10],
        [0.01, 10, 0.5, 10],
    ]
    # Strict landmarks with a softer morph
    landmarks_soft = [
        [0.01, 10, 0.5, 10],
        [0.01, 10, 0.5, 10],
        [0.01, 10, 0.5, 10],
        [0.008, 10, 1.5, 10],
    ]
    # Ramping landmark strictness with a soft morph
    landmarks_ramp_soft = [
        [0.01, 0, 0.5, 10],
        [0.02, 2, 0.5, 10],
        [0.03, 5, 0.5, 10],
        [0.01, 8, 0.5, 10],
        [0.005, 10, 0.5, 10],
    ]

    am = MeshMorph.AmbergMapping(source, target, output, lpairs=lpairs, steps=landmarks_ramp_soft, gamma=1)

    output = am.mapped
    output.save_trimesh_as_stl()
    return output


def morph_liner_internal_surface(unmapped: MeshObj.STLMesh, mapped: MeshObj.STLMesh):
    """Performs the morhphing of the full liner mesh based on the unmapped to
    mapped liner surface meshes."""
    # Generate interpolation matrix and coefficients materix for the morph
    morph = RBFMorpher(unmapped, mapped, MeshMorph.custom_RBF)

    inp_liner_mesh = MeshObj.LinerINPMesh('Liner Mesh',
                                          'LinerMesh',
                                          os.path.join(WDIR, FOLDER))

    # Morph the liner nodes and replace them in the liner mesh objected
    inp_liner_mesh.nodes[:,1:] = morph.morph_vertices(inp_liner_mesh.nodes[:,1:])

    inp_liner_mesh.write_inp('LinerMeshMorphed.inp')

    # Also morph the surface mesh of the liner inp with the specified thickness
    inp_liner_volume_mesh = MeshObj.LinerINPMesh('Liner Surface Volume',
                                                 'LinerSurfaceVolume',
                                                 os.path.join(WDIR, FOLDER))

    inp_liner_volume_mesh.write_stl()

    inp_liner_volume_mesh.nodes[:,1:] = morph.morph_vertices(inp_liner_volume_mesh.nodes[:,1:])

    inp_liner_volume_mesh.rename('MorphedLinerMeshSurfaceVolume')
    inp_liner_volume_mesh.write_inp('MorphedLinerMeshSurfaceVolume.inp')
    inp_liner_volume_mesh.write_stl()

def liner_to_skin_map(new_map=False, new_liner=True):
    if not new_map and os.path.isfile(os.path.join(WDIR, FOLDER, 'LinerSurfaceMorphed.stl')):
        liner_surface_mapped = MeshObj.STLMesh('Liner Surface Mesh',
                                               'LinerSurfaceMorphed',
                                               os.path.join(WDIR, FOLDER),
                                               description='Unmorphed liner surface mesh')
    else:
        # Load skin mesh by name of manually cut mesh or by cutting the base skin
        # mesh
        skin = MeshObj.STLMesh(name='Skin Mesh',
                                f_name='skin_m_aligned_cut',
                                f_folder=os.path.join(WDIR, 'Liner Model'))
        # skin = MeshObj.cut_mesh(skin, custom_cut=[0.210, [-0.3645, 0.0, 0.9166]]) # For z aligned
        #[skin] = MeshObj.cut_meshes([skin], custom_cut=[0.210, [-0.3645, 0.9166, 0.0]]) # for y aligned

        # Load unmapped liner_surface
        liner_surface = load_liner_surface(from_inp=new_liner)

        # Apply alignment translation used for amberg mapping not for RBFMorpher
        t_matrix = MeshObj.translation_matrix([0, 0.06, 0]) # 0.06 is half the diameter of the liner
        amberg_liner_surface = liner_surface.copy_mesh('amberg_liner_surface','AmbergLinerSurface')
        amberg_liner_surface.apply_transformation(t_matrix)

        # This might rely on the boundary nodes of the liner mesh being ordered in a specific way.
        liner_rim_nodes = amberg_liner_surface.order_rim_nodes()

        num_rim_nodes = len(liner_rim_nodes['indices'])

        skin_rim_nodes = skin.resample_rim_nodes(num_rim_nodes)

        # For plotting the polygon to check if the process runs correctly
        #fig = plt.figure()
        #ax = fig.add_subplot(projection='3d')
        #for i, node in enumerate(liner_rim_nodes['coords']):
        #    ax.scatter(node[0], [node[1]], [node[2]], label=str(i))
        #for i, node in enumerate(skin_rim_nodes['coords']):
        #    ax.scatter(node[0], [node[1]], [node[2]], label=str(i))
        #plt.xlabel('X')
        #plt.ylabel('Y')
        #ax.set_zlabel('Z')
        #plt.legend()
        #plt.show()

        landmarks = [[node_num, skin_rim_nodes['coords'][i]] \
                        for i, node_num in enumerate(liner_rim_nodes['indices'])]

        # Landmarks format:
        # [[node index of mesh to be morphed,
        #   [x_coordinate to morph to, y_coordinate to morph to, z_coordinate to morph to]]]

        # If needed you can add some manual landmarks for other locations. 
        manual_landmarks = []
        #manual_landmarks = [
        #    [1660, [41.1649, 114.04, -46.876]],
        #    [2027, [55.4545, 144.949, -13.7508]],
        #    [1989, [-45.3078, 129.846, 2.14974]],
        #]

        for l in manual_landmarks:
            landmarks.append(l)

        # Map the liner surface to the skin mesh
        liner_surface_mapped = amberg_map_liner(amberg_liner_surface, skin, lpairs=landmarks)
    return liner_surface_mapped

if __name__ == "__main__":
    # Get liner to skin surface map
    liner_surface_mapped = liner_to_skin_map(new_map=False)

    # Load unmapped liner_surface
    liner_surface = load_liner_surface(from_inp=False)

    # Morph the liner mesh using the unmapped to mapped radial bias morph.
    morph_liner_internal_surface(liner_surface, liner_surface_mapped)
    # This morph_liner morphs the original LinerMesh as well as a mesh with just the surface

    # STL mesh of the morphed liner mesh without internal geometry to use as saurce for second morph
    liner_volume_surface_morphed_1 = MeshObj.STLMesh('MorphedLinerMeshSurfaceVolume',
                                        'MorphedLinerMeshSurfaceVolume',
                                        os.path.join(WDIR, FOLDER),
                                        load=True)

    # STL of the skin and offset geometry to use as target for second morph
    liner_offset_volume_mesh = MeshObj.STLMesh('Offset Mesh',
                                               'liner5mm_m_aligned_cut_with_skin_joined',
                                               os.path.join(WDIR, FOLDER, 'LinerMorph_5mm_v2'))

    # Result of amberg morphing the two meshes above, this results in an STL
    # mesh with correspondence to the liner surface mesh and the shape of the
    # skin and liner offset geometry.
    liner_volume_surface_mapped = amberg_map_liner(liner_volume_surface_morphed_1,
                                                   liner_offset_volume_mesh,
                                                   output_name='LinerSurfaceVolumeMorphed')

    # Morph of the morphed liner mesh based on the second amberg mapping
    morph = RBFMorpher(liner_volume_surface_morphed_1,
                       liner_volume_surface_mapped, MeshMorph.custom_RBF)

    # Morph vertices of the morphed liner mesh with the second morph
    inp_liner_mesh = MeshObj.LinerINPMesh('Liner Mesh',
                                          'LinerMeshMorphed',
                                          os.path.join(WDIR, FOLDER))

    # Morph the liner nodes and replace them in the liner mesh objected
    inp_liner_mesh.nodes[:,1:] = morph.morph_vertices(inp_liner_mesh.nodes[:,1:])

    inp_liner_mesh.write_inp('LinerMeshMorphed_2.inp')
