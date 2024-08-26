# test_pytest_unittest.py

import src.MeshObj as mesh
import numpy as np

def test_meshobj_transformations():
    assert mesh.rot_x(90) == np.array([[1, 0, 0, 0],
                                      [0, 0, -1, 0],
                                      [0, 1, 0, 0],
                                      [0, 0, 0, 1]])
    assert mesh.rot_y(90) == np.array([[0, 0, 1, 0],
                                      [0, 1, 0, 0],
                                      [-1, 0, 0, 0],
                                      [0, 0, 0, 1]])
    assert mesh.rot_z(90) == np.array([[0, -1, 0, 0],
                                      [1, 0, 0, 0],
                                      [0, 0, 1, 0],
                                      [0, 0, 0, 1]])
    assert mesh.rot_x(0) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]])
    assert mesh.rot_y(0) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]])
    assert mesh.rot_z(0) == np.array([[1, 0, 0, 0],
                                     [0, 1, 0, 0],
                                     [0, 0, 1, 0],
                                     [0, 0, 0, 1]])
    assert mesh.translation_matrix([0, 0, 0]) == np.array([[1, 0, 0, 0],
                                                          [0, 1, 0, 0],
                                                          [0, 0, 1, 0],
                                                          [0, 0, 0, 1]])
    assert mesh.translation_matrix([10, 20, 30]) == np.array([[1, 0, 0, 10],
                                                             [0, 1, 0, 20],
                                                             [0, 0, 1, 30],
                                                             [0, 0, 0, 1]])
    assert mesh.scaling_matrix(1) == np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0],
                                              [0, 0, 1, 0],
                                              [0, 0, 0, 1]])
    assert mesh.scaling_matrix(185) == np.array([[185, 0, 0, 0],
                                                [0, 185, 0, 0],
                                                [0, 0, 185, 0],
                                                [0, 0, 0, 1]])
  
