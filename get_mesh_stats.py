import numpy as np
import scipy.sparse as sparse
import pymeshlab as mlab
from src.pytetgen import read_tetgen,call_tetgen
import os
from os.path import basename

def get_geom_stats(ms):
    '''Computes geometric information from a surface mesh'''
    geom  = ms.get_geometric_measures()
    avg_edge_length = geom['avg_edge_length']
    mesh_volume = geom['mesh_volume']
    surface_area = geom['surface_area']
    return surface_area,mesh_volume,avg_edge_length

def find_mesh_quality(tet_file):
    '''Finds the quality of a finite element mesh by finding the propotion of elements with a condition number greater than 0.5.
    Condition number is defined as in:

    Knupp, Patrick. Matrix norms and the condition number: A general framework to improve mesh quality via node-movement. 
    No. SAND99-2542C. Sandia National Lab.(SNL-NM), Albuquerque, NM (United States); 
    Sandia National Lab.(SNL-CA), Livermore, CA (United States), 1999.
    
    '''
    nodes, elements = read_tetgen(tet_file)
    W = np.array([[1 , .5 , .5], [0 , np.sqrt(3)/2, np.sqrt(3)/6 ],[0,0,np.sqrt(2/3)]])
    Winv = np.linalg.inv(W) 
    A =lambda e: np.vstack((nodes[e[1]] - nodes[e[0]],nodes[e[2]] - nodes[e[0]],nodes[e[3]] - nodes[e[0]])).T
    frob_norm = lambda x: np.sqrt(np.trace(np.matmul(x,x.T)))
    kappa =lambda A: frob_norm(np.matmul(A,Winv))*frob_norm(np.matmul(W,np.linalg.inv(A)))
    shape_measures = [3/kappa(A(e)) for e in elements]
    mesh_quality = np.mean(np.array(shape_measures) > 0.5)
    return mesh_quality


def mesh_stats(swc,ms,ms_alpha,mesh_name):
    '''Function to compute relevent summary data to be stored as a dictionary'''
    # Store mesh data from final mesh
    surface_area,mesh_volume,_ = get_geom_stats(ms)
    n_v = ms.current_mesh().vertex_number()
    n_f =  ms.current_mesh().face_number()
    ms.clear()
    # Store mesh data from alpha mesh
    alpha_surface_area,alpha_mesh_volume,_ = get_geom_stats(ms_alpha)
    alpha_n_v = ms_alpha.current_mesh().vertex_number()
    alpha_n_f =  ms_alpha.current_mesh().face_number()

     # Check volume mesh
    print('Checking tetgen')
    timings = swc.timings
    # Time tetgen
    tet_output = call_tetgen(mesh_name,'-pq1.2a1.0O9/7VCBF')
    print(tet_output)
    _,b = tet_output.split('Total running seconds: ')
    tetgen_time = float(b.split('\n')[0])
    timings['tetgen'] = tetgen_time

    # Find mesh quality
    print('Finding mesh quality')
    tet_file = mesh_name.replace('.ply','.1')
    mesh_quality = find_mesh_quality(tet_file)
    mesh_stats = {
            'morphology' : basename(swc.file).replace('.swc',''),
            'vertex_number' : [n_v],
            'face_number' : [n_f],
            'surface_area' : [surface_area],
            'volume' : [mesh_volume],
            'alpha_vertex_number' : [alpha_n_v],
            'alpha_face_number' : [alpha_n_f],
            'alpha_surface_area' : [alpha_surface_area],
            'alpha_volume' : [alpha_mesh_volume],
            'mesh_quality' : [mesh_quality],
            'cleaned_swc_nodes' : [len(swc.type_data)]
        }
    data = {**mesh_stats,**timings}
    print(f'Removing tetgen files {tet_file}')
    for ext in ['.node','.ele','.smesh']:
        os.remove(tet_file+ext)
    return data