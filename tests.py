import pytest
from src import Swc, call_tetgen, is_watertight
import numpy
import os
import pymeshlab as mlab

def test_tetgen():
    """Test TetGen verifies watertightness."""

    file = "test_data/test.ply"
    output = call_tetgen(file, args="-d")
    assert "No faces are intersecting." in output

def test_watertightness_check():
    """Test watertightness is verified."""

    file = "test_data/test.ply"
    ms  = mlab.MeshSet()
    ms.load_new_mesh(file)
    assert is_watertight(ms)


def test_node_processing():
    """"Test node processing against known output"""

    file = "test_data/test.swc"
    cleaned_file = "test_data/test_clean.swc"
    swc = Swc(file, process=True, Delta=15.0)
    swc_clean = Swc(cleaned_file, process=False)
    assert len(swc.type_data) == len(swc_clean.type_data)
    assert numpy.linalg.norm(swc.position_data - swc_clean.position_data) < 1e-12
    assert numpy.linalg.norm(swc.radius_data - swc_clean.radius_data) < 1e-12
    assert numpy.linalg.norm(swc.type_data - swc_clean.type_data) < 1e-12
    assert numpy.linalg.norm(swc.conn_data - swc_clean.conn_data) < 1e-12

def test_meshing():
    """Test meshing algorithm.
    """
    # Load Swc
    file = "test_data/test2.swc"
    swc = Swc(file)
    # Make mesh
    swc.make_mesh(simplify=False)
    # Check mesh has been made
    if os.path.isfile("test_data/test2.ply"):
        os.remove("test_data/test2.ply")
        assert True
    else:
        assert False
