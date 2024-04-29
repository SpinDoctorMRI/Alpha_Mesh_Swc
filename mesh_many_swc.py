from src import Swc
import argparse
import time
import os
import pymeshlab as mlab
from datetime import datetime

if __name__ =='__main__':
    description = """Reads swc files from a directory and produces coarse watertight surface meshs"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", help="Input SWC directory.")
    parser.add_argument("--output_dir",help="Output directory for meshes")
    args = parser.parse_args()
    input_dir = str(args.input_dir)
    print(os.getcwd())
    files = os.listdir(input_dir)
    output = args.output_dir

    if output is None:
        log_file = os.path.join('log.txt')
    else:
        log_file = os.path.join(output,'log.txt')

    if not(os.path.isfile(log_file)):
        with open(log_file,'w') as f:
            f.write(f'# Log file for {input_dir} at {datetime.now()} \n')
            f.write(f'# Cell name | Mesh computation time (s) | number of vertices | number of faces | bad triangle ratio \n')


    for file in files:
        cellname = os.path.basename(file).replace('.swc','')
        if output is not None:
            output_file = os.path.join(output,cellname+".ply")
        else:
            output_file = os.path.join(input_dir,cellname+".ply")
        print(f'Meshing {cellname}')

        if not(os.path.isfile(output_file)):
            start = time.time()
            swc = Swc(os.path.join(input_dir,file),True,2.0,1.0)
            ms = swc.make_mesh(simplify=True,output_dir=output)
            ms.compute_scalar_by_aspect_ratio_per_face(metric='inradius/circumradius')
            aspect_ratios = ms.current_mesh().face_scalar_array()
            bad_triangle_ratio = sum(aspect_ratios < 0.3)/len(aspect_ratios)
            with open(log_file,'a') as f:
                f.write(f'{cellname} {time.time()-start:.2f} {ms.current_mesh().vertex_number()} {ms.current_mesh().face_number()} {bad_triangle_ratio}\n')
        print(f'Completed {cellname}')

