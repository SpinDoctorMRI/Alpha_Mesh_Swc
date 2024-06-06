import matplotlib.pyplot as plt
import numpy as np
import itertools
import scipy.sparse as sparse
import pymeshlab as mlab

def get_bad_triangle_ratio(ms):
    '''Computes the proportion of skinny triangles in a surface mesh'''
    ms.compute_scalar_by_aspect_ratio_per_face(metric='inradius/circumradius')
    aspect_ratios = ms.current_mesh().face_scalar_array()
    bad_triangle_ratio = sum(aspect_ratios < 0.1)/len(aspect_ratios)
    return bad_triangle_ratio

def get_min_edge_length(ms):
    '''Computes the minimum edge length in a surface mesh'''
    edge_matrix = sparse.dok_array((ms.current_mesh().vertex_number(),ms.current_mesh().vertex_number()),dtype = int)
    faces = ms.current_mesh().face_matrix()
    for f in faces:
        edges = itertools.combinations(f,2)
        for edge in edges:
            edge_matrix[edge[0],edge[1]] = 1
    vertices = ms.current_mesh().vertex_matrix()
    edges = edge_matrix.keys()
    edge_lengths = [np.linalg.norm(vertices[e[0]] - vertices[e[1]]) for e in edges]
    return min(edge_lengths)

def get_other_stats(ms):
    '''Computes geometric information from a surface mesh'''
    geom  = ms.get_geometric_measures()
    avg_edge_length = geom['avg_edge_length']
    mesh_volume = geom['mesh_volume']
    surface_area = geom['surface_area']
    return surface_area,mesh_volume,avg_edge_length