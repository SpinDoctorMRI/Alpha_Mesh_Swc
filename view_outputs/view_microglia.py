import numpy as np
import trimesh as tm
from trimesh import viewer,Trimesh
import argparse
from view_swc import draw_swc
import pymeshlab as mlab
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


if __name__ == "__main__":

    description = """Reads a SWC file and surface mesh and visualize using trimesh."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", help="Input cell name.")
    args = parser.parse_args()
    
    primitives = draw_swc(args.input+".swc")
    ms = mlab.MeshSet()
    ms.load_new_mesh(args.input+'.ply')
    soma = mlab2tmesh(ms)
    primitives.append(soma)
    scene = tm.scene.Scene(primitives)
    viewer = tm.viewer.windowed.SceneViewer(scene, flags={"wireframe": False})