# -*- coding: utf-8 -*-
import pytest
import numpy as np
from HexMeshMorpher.RBF_morpher import RBFMorpher, custom_RBF
from unittest.mock import MagicMock

# test_pytest_unittest.py
class MockMesh:
    """Mock class for MeshObj.STLMesh."""
    def __init__(self, vertices):
        self.trimesh = MagicMock()
        self.trimesh.vertices = vertices

def test_generate_interpolation_matrix():
    # Mock data for original and displaced meshes
    original_vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    displaced_vertices = np.array([[0, 0, 0], [1, 1, 0], [0, 1, 1]])

    original_mesh = MockMesh(original_vertices)
    displaced_mesh = MockMesh(displaced_vertices)

    # Instantiate RBFMorpher with the custom RBF function
    morpher = RBFMorpher(original_mesh, displaced_mesh, custom_RBF)

    # Expected interpolation matrix
    expected_matrix = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            expected_matrix[i][j] = custom_RBF(
                np.linalg.norm(original_vertices[i] - original_vertices[j])
                )

    # Assert that the generated interpolation matrix matches the expected matrix
    np.testing.assert_array_almost_equal(morpher.interp_matrix, expected_matrix)

def test_generate_coefficient_matrix():
    # Mock data for original and displaced meshes
    original_vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
    displaced_vertices = np.array([[0, 0, 0], [1, 1, 0], [0, 1, 1]])

    original_mesh = MockMesh(original_vertices)
    displaced_mesh = MockMesh(displaced_vertices)

    # Instantiate RBFMorpher with the custom RBF function
    morpher = RBFMorpher(original_mesh, displaced_mesh, custom_RBF)

    # Manually compute the expected coefficient matrix
    interp_matrix = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            interp_matrix[i][j] = custom_RBF(
                np.linalg.norm(original_vertices[i] - original_vertices[j])
                )
    expected_coeff_matrix = np.linalg.inv(interp_matrix) @ (displaced_vertices - original_vertices)

    # Assert that the generated coefficient matrix matches the expected matrix
    np.testing.assert_array_almost_equal(morpher.coeff_matrix, expected_coeff_matrix)
