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
    """

    tmesh = mlab2tmesh(ms)
    ms.compute_selection_by_self_intersections_per_face()
    num_intersections = ms.current_mesh().selected_face_number()
    return tmesh.is_watertight  and (num_intersections == 0)

def simplify_mesh_first(ms,targetfacenum):
    """Apply iterative remeshing to simplify mesh using quadric edge collapse
    
    Args:
        ms (mlab.MeshSet): mesh
    
    """
    # Apply edge collapse
    old_number = ms.current_mesh().face_number()
    ms.meshing_decimation_quadric_edge_collapse(targetfacenum = int(targetfacenum),preservetopology  = True,planarquadric=True,qualitythr = 0.3)
    new_number = ms.current_mesh().face_number()
    print(f'Old number of faces = {old_number} ,new number of faces = {new_number}')
    flag = is_watertight(ms)

    return ms,flag

def simplify_mesh_further(ms,targetfacenum,r_min):
    """Apply iterative remeshing to simplify mesh using quadric edge collapse
    
    Args:
        ms (mlab.MeshSet): mesh
    
    """
    # Apply edge collapse
    old_number = ms.current_mesh().face_number()
    d = ms.get_geometric_measures()
    bbox = d['bbox']
    ms.meshing_isotropic_explicit_remeshing(
                iterations = 7,
                adaptive = True,
                targetlen = mlab.PercentageValue(100*r_min/bbox.diagonal()),
                checksurfdist = False
            )
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
    new_number = ms.current_mesh().face_number()
    print(f'Old number of faces = {old_number} ,new number of faces = {new_number}')
    return ms,flag

def simplify_mesh(ms,dfaces,r_min,alpha_fraction):
    print('Applying first simplification')
    attempt = 1
    flag = False
    ms_cp = dcp_meshset(ms)
    while not(flag) and attempt < 16:
        if attempt*dfaces > ms.current_mesh().face_number():
            break
        print(f'Applying simplification, attempt = {attempt}')
        ms,flag = simplify_mesh_first(ms,attempt*dfaces)
        attempt+= 1
        if not(flag):
            ms = dcp_meshset(ms_cp)

    if not(flag):
        print('First simplification failed, try with coarser alpha mesh')
        ms.generate_alpha_wrap(alpha_fraction = 5*alpha_fraction,offset_fraction =alpha_fraction/30)
        attempt = 1
        flag = False
        ms_cp = dcp_meshset(ms)
        while not(flag) and attempt < 16:
            if attempt*dfaces > ms.current_mesh().face_number():
                break
            print(f'Applying simplification, attempt = {attempt}')
            ms,flag = simplify_mesh_first(ms,attempt*dfaces)
            attempt+= 1
            if not(flag):
                ms = dcp_meshset(ms_cp)

    print('Applying second simplification')
    attempt = 1
    flag = False
    dfaces = 2*dfaces
    ms_cp = dcp_meshset(ms)
    while not(flag) and attempt < 16:
        if attempt*dfaces > ms.current_mesh().face_number():
            break
        print(f'Applying simplification, attempt = {attempt}')
        ms,flag = simplify_mesh_further(ms,attempt*dfaces,r_min)
        attempt+= 1
        if not(flag):
            ms = dcp_meshset(ms_cp)
    return ms

