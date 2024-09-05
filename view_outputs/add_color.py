import sys
import pymeshlab as mlab
if __name__=='__main__':
    '''Add color to mesh so that it can be seen better with open3d'''
    file = sys.argv[1]
    ms = mlab.MeshSet()
    ms.load_new_mesh(file)
    ms.compute_scalar_by_function_per_vertex(q='z',normalize=True)
    ms.compute_color_from_scalar_per_vertex(colormap='Plasma')
    ms.save_current_mesh(file,binary=False)