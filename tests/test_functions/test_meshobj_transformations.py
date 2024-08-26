# test_pytest_unittest.py

import src.HexMeshMorpher.MeshObj as mesh
import numpy as np

def test_meshobj_transformations():
    assert (mesh.rot_x(90).astype(float) == np.array([[1, 0, 0, 0],
                                      [0, 0, -1, 0],
                                      [0, 1, 0, 0],
                                      [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.rot_y(90).astype(float) == np.array([[0, 0, 1, 0],
                                      [0, 1, 0, 0],
                                      [-1, 0, 0, 0],
                                      [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.rot_z(90).astype(float) == np.array([[0, -1, 0, 0],
                                      [1, 0, 0, 0],
                                      [0, 0, 1, 0],
                                      [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.rot_x(0).astype(float) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.rot_y(0).astype(float) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.rot_z(0).astype(float) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.translation_matrix([0, 0, 0]).astype(float) == np.array([[1, 0, 0, 0],
                                                          [0, 1, 0, 0],
                                                          [0, 0, 1, 0],
                                                          [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.translation_matrix([10, 20, 30]).astype(float) == np.array([[1, 0, 0, 10],
                                                             [0, 1, 0, 20],
                                                             [0, 0, 1, 30],
                                                             [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.scaling_matrix(1).astype(float) == np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0],
                                              [0, 0, 1, 0],
                                              [0, 0, 0, 1]]).astype(float)).all()
    assert (mesh.scaling_matrix(185).astype(float) == np.array([[185, 0, 0, 0],
                                                [0, 185, 0, 0],
                                                [0, 0, 185, 0],
                                                [0, 0, 0, 1]]).astype(float)).all()
  
