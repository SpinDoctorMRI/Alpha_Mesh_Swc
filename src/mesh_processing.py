import numpy as np
import pymeshlab as mlab
from trimesh import Trimesh

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



def is_watertight(ms):
    """Check whether the mesh is watertight using trimesh routine.

    Args:
        ms (mlab.Mesh or mlab.MeshSet): mesh.
    Returns:
        flag: (bool) flag for surface being watertight.
    """

    tmesh = mlab2tmesh(ms)
    ms.compute_selection_by_self_intersections_per_face()
    num_intersections = ms.current_mesh().selected_face_number()
    return tmesh.is_watertight  and (num_intersections == 0)

def simplify_mesh_first(ms,targetfacenum):
    """Apply iterative remeshing to simplify mesh using quadric edge collapse
    
    Args:
        ms (mlab.MeshSet): mesh
    Returns:
        ms: (MeshSet)
        flag: (bool) flag for surface being watertight.
    """
    # Apply edge collapse
    old_number = ms.current_mesh().face_number()
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum = int(targetfacenum),preservetopology  = True,planarquadric=True,qualitythr = 0.3)
    new_number = ms.current_mesh().face_number()
    print(f'Old number of faces = {old_number} ,new number of faces = {new_number}')
    flag = is_watertight(ms)

    return ms,flag

def simplify_mesh_further(ms,targetfacenum,r_min):
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
    flag = is_watertight(ms)
    
    return ms,flag

def simplify_mesh(ms,dfaces,r_min,min_faces):
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


    print('Applying first simplification')
    
    
    # Initial isotropic remeshing step.
    attempt = 1 
    flag = False
    dfaces = 2*dfaces
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
    while not(flag) and attempt < 50:
        if attempt*dfaces > ms.current_mesh().face_number():
            agg_simp_terminated = True
            break
        print(f'Applying simplification, attempt = {attempt}')
        
        ms,flag = simplify_mesh_further(ms,(attempt-1)*dfaces + min_faces,r_min)
        new_number = ms.current_mesh().face_number()
        print(f'Old number of faces = {old_number} ,new number of faces = {new_number}, watertight = {flag}')
        attempt+= 1
        if not(flag):
            ms = dcp_meshset(ms_cp)
    
    # If previous attempt failed, conduct emergency remeshing on the original mesh.
    if (attempt == 50 and not(flag)) or agg_simp_terminated:
        ms = dcp_meshset(ms_alpha)
        print('Emergency remeshing')
        attempt = 1
        flag = False
        ms_cp = dcp_meshset(ms)
        while not(flag):
            if attempt*dfaces > 2*ms.current_mesh().face_number()/3:
                break
            print(f'Applying simplification, attempt = {attempt}')
            ms,flag = simplify_mesh_first(ms,(attempt-1)*dfaces + min_faces)
            attempt+= 1
            if not(flag):
                ms = dcp_meshset(ms_cp)

    # Return ms, the smallest watertight mesh we can construct from the original.
    return ms

