from src import Swc
import argparse
import time
import pymeshlab as mlab
import os
if __name__ =='__main__':
    description = """Takes refined watertight mesh and outputs a coarse watertight surface mesh"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="Input SWC file.")
    parser.add_argument("meshfile", help="Input mesh file.")
    parser.add_argument("--output_dir",help="Output directory for mesh")
    parser.add_argument("--min_faces",help="Minimum number of faces for the mesh",default=None)
    parser.add_argument("--dfaces",help="Amount to change target number of faces by if failure.",default=None)
    
    args = parser.parse_args()

    file = args.file
    meshfile =args.meshfile
    output_dir = args.output_dir
    temp_dir=os.path.join(output_dir,'test')
    meshname = output_dir + '/' + os.path.basename(meshfile)
    start = time.time()

    swc = Swc(file,False)
    ms = mlab.MeshSet()
    print('Loading mesh')
    ms.load_new_mesh(meshfile)
    print('Mesh loaded: beginning simplfication')
    ms = swc._simplify_mesh(ms,args.min_faces,args.dfaces,temp_dir)


    print('Simplification complete')
    ms.save_current_mesh(meshname,binary=False)
    print(f'Total Elapsed time = {time.time()-start:.2f}')

