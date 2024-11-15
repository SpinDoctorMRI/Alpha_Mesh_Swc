from src import Swc
import argparse
import time
import pymeshlab as mlab
import os
if __name__ =='__main__':
    description = """Reads swc file and produces a watertight surface mesh for the soma"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="Input SWC file.")
    parser.add_argument("--output_dir",help="Output directory for mesh")

    args = parser.parse_args()

    file = args.file
    output_dir = args.output_dir
    filename = os.path.basename(file).replace('.CNG','')
    if output_dir is None:
        output_dir = os.path.dirname(file)
    meshname = output_dir+'/'+filename.replace('.swc','_soma.ply')


    start = time.time()
    
    # Take swc file input and remove non-soma nodes
    swc = Swc(file,False)
    soma_indices = swc.type_data == 1
    swc.position_data = swc.position_data[soma_indices]
    swc.radius_data = swc.radius_data[soma_indices]
    swc.conn_data = swc.conn_data[soma_indices]
    swc.type_data = swc.type_data[soma_indices]
    swc.initialise_branches()
    swc.timings = {}

    # Create initial mesh
    ms_soma = swc._build_initial_mesh()
    print('Mesh initialised')
    ms_soma.generate_alpha_wrap(alpha_fraction = 0.005,offset_fraction =0.005/60)
    print('Alpha wrap applied')

    ms_soma.save_current_mesh(meshname,binary=False)
    print(f'Total Elapsed time = {time.time()-start:.2f}')
