import pymeshlab as mlab
import trimesh as tm
from trimesh import viewer,Trimesh
import sys 
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

if __name__=='__main__':
    '''View a .ply file'''
    ms = mlab.MeshSet()
    ms.load_new_mesh(sys.argv[1])
    t = mlab2tmesh(ms)
    scene = tm.scene.Scene(t)
    viewer = tm.viewer.windowed.SceneViewer(scene, flags={"wireframe": False})
