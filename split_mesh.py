import pymeshlab as mlab
import os
import sys

if __name__=='__main__':
    file = sys.argv[1]
    cell = os.path.basename(file).replace('.ply','')
    output_dir =  sys.argv[2]
    ms = mlab.MeshSet()
    ms.load_new_mesh(file)
    ms.generate_splitting_by_connected_components(delete_source_mesh =True)
    n = ms.mesh_number()
    for i in range(1,n+1):
        ms.set_current_mesh(i-1)
        ms.save_current_mesh(os.path.join(output_dir,cell)+f'_{i}.ply',binary=False)
