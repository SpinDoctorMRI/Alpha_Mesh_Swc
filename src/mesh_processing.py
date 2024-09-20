import numpy as np
import pymeshlab as mlab
from trimesh import Trimesh
import os
from .pytetgen import call_tetgen
import warnings

def dcp_meshset(meshset):
    """Make a deepcopy of mlab.MeshSet."""

    ms = mlab.MeshSet()
    ms.add_mesh(meshset.current_mesh())

    return ms


def mlab2tmesh(ms):
    """Convert Meshlab mesh to Trimesh object.

    Args:
        ms (mlab.MeshSet, mlab.Mesh): Meshlab mesh.

    Raises:
        TypeError: wrong mesh type.

    Returns:
        Trimesh: Trimesh object.
    """

    # check mesh type
    if isinstance(ms, mlab.MeshSet):
        m = ms.current_mesh()
    elif isinstance(ms, mlab.Mesh):
        m = ms
    else:
        raise TypeError("Unknown mesh type.")

    # convert mlab.Mesh to Trimesh
    tmesh = Trimesh(
        process=False,
        use_embree=False,
        vertices=m.vertex_matrix(),
        faces=m.face_matrix(),
        face_normals=m.face_normal_matrix(),
        vertex_normals=m.vertex_normal_matrix(),
        vertex_colors=m.vertex_color_matrix()
    )

    return tmesh



def is_watertight(ms,name=None):
    """Check whether the mesh is watertight using trimesh routine and tetgen.

    Args:
        ms (mlab.Mesh or mlab.MeshSet): mesh.
    Returns:
        flag: (bool) flag for surface being watertight.
    """
    # Apply a quick check using trimesh. 
    tmesh = mlab2tmesh(ms)
    
    # if not(tmesh.is_watertight):
    #     # Quick check but may have false negative, so check with tetgen
    #     return is_watertight_tetgen(ms)
    # else:
    #     return  True
    print('Checking self-intersections with TetGen')
    try:
        no_self_intersections=is_watertight_tetgen(ms,name)
    except ImportError as e:
        print(repr(e))
        warnings.warn('Appplying PymeshLab filter instead. Accuracy may be lower.')
        ms.compute_selection_by_small_disconnected_components_per_face()
        no_self_intersections= ms.current_mesh().selected_face_number() == 0
        
    flag = tmesh.is_watertight and no_self_intersections

    return flag

def is_watertight_tetgen(ms,temp_dir_name):
    """Check whether the mesh is watertight using tetgen routine.

    Args:
        ms (mlab.Mesh or mlab.MeshSet): mesh.
    Returns:
        flag: (bool) flag for surface being watertight.
    """
    dir = os.path.join(os.getcwd(),temp_dir_name)
    print(f'Making {dir}')
    os.mkdir(dir)
    ms.save_current_mesh(os.path.join(dir,'test.ply'),binary=False)
    output =   call_tetgen(os.path.join(dir,'test.ply'),'-dBENF')
    print(f'Removing {dir}')
    for file in os.listdir(dir):
        os.remove(os.path.join(dir,file))
    os.rmdir(dir)
    if not('Delaunizing vertices...' in output):
        raise ImportError(f'TetGen not working. Check file permissions and the paths are correct.')
    return 'No faces are intersecting.' in output

def simplify_mesh_further(ms,targetfacenum,r_min,temp_dir_name):
    """Apply remeshing to simplify mesh using quadric edge collapse
    
    Args:
        ms (mlab.MeshSet): mesh
    Returns:
        ms: (MeshSet)
    
    """
    # Apply edge collapse
    
    ms.meshing_decimation_quadric_edge_collapse(
        targetfacenum=int(targetfacenum),
        preservetopology  = True,
        qualityweight=True,
        preservenormal=True,
        qualitythr=0.3,
        planarquadric=True,
        planarweight=0.002
        )
    flag = is_watertight(ms,temp_dir_name)
    
    return ms,flag

def simplify_mesh(ms,dfaces=1000,r_min=0.1,min_faces=2000,temp_dir_name=None):
    '''Apply remeshing using quadric edge collapse and isotropic remeshing to reduce the number of vertices
    Given a initially very small target number of faces, we remesh the surface mesh to have that number of faces. 
    If it is watertight, this mesh is returned. Else, the target number of faces is increased by a fixed increment and the original mesh is remeshed to this target.

    Args:
        ms: (MeshSet)
        dfaces: (int) increments to increase the desired number of faces until a watertight mesh is produced.
        r_min: (float) minimum cross-sectional radius of the swc file.
        min_faces: (int) initial number of target faces.
    Returns:
        ms: (MeshSet)
    
    '''
    
    # Save the original mesh
    ms_alpha = dcp_meshset(ms)

    if temp_dir_name == None:
        warnings.warn("Making temp directory in current directory")
        temp_dir_name = os.path.join(os.getcwd(),'temp')
    print('Applying isotropic remeshing')
    
    
    # Initial isotropic remeshing step.
    attempt = 1 
    flag = False
    old_number = ms.current_mesh().face_number()
    d = ms.get_geometric_measures()
    bbox = d['bbox']
    ms.meshing_isotropic_explicit_remeshing(
                iterations = 7,
                adaptive = True,
                targetlen = mlab.PercentageValue(100*r_min/bbox.diagonal()),
                checksurfdist = False
            )
    
    # Save new mesh
    ms_cp = dcp_meshset(ms)

    # Attempt aggressive simplification on the new mesh.
    agg_simp_terminated = False
    new_number = 0
    while not(flag) and attempt < 15:
        if new_number> old_number:
            agg_simp_terminated = True
            break
        print(f'Applying simplification, attempt = {attempt}')
        
        ms,flag = simplify_mesh_further(ms,(attempt-1)*dfaces + min_faces,r_min,temp_dir_name)
        new_number = ms.current_mesh().face_number()
        print(f'Old number of faces = {old_number} ,new number of faces = {new_number}, watertight = {flag}')
        attempt+= 1
        if not(flag):
            ms = dcp_meshset(ms_cp)
    
    # If previous attempt failed, conduct emergency remeshing on the original mesh.
    if (attempt == 15 and not(flag)) or agg_simp_terminated:
        ms = dcp_meshset(ms_alpha)
        print('Emergency remeshing')
        attempt = 1
        flag = False
        ms_cp = dcp_meshset(ms)
        while not(flag):
            if attempt*dfaces > 2*ms.current_mesh().face_number()/3:
                break
            print(f'Applying simplification, attempt = {attempt}')
            ms,flag = simplify_mesh_further(ms,(attempt-1)*dfaces + min_faces,r_min,temp_dir_name)
            new_number = ms.current_mesh().face_number()
            print(f'Old number of faces = {old_number} ,new number of faces = {new_number}, watertight = {flag}')
            attempt+= 1
            if not(flag):
                ms = dcp_meshset(ms_cp)

    # Return ms, the smallest watertight mesh we can construct from the original.
    # only keep the largest component
    ms.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.99)
    ms.meshing_remove_selected_vertices_and_faces()
    return ms

