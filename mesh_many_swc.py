from src import Swc
import argparse
import time
import os
import pymeshlab as mlab
from datetime import datetime
from src.mesh_stats_func import get_bad_triangle_ratio,get_min_edge_length,get_other_stats


# Takes as input a directory of swc files and produces surface meshes for each one.
if __name__ =='__main__':
    description = """Reads swc files from a directory and produces coarse watertight surface meshs"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", help="Input SWC directory.")
    parser.add_argument("--output_dir",help="Output directory for meshes")
    args = parser.parse_args()
    input_dir = str(args.input_dir)
    print(os.getcwd())
    files = os.listdir(input_dir)
    
    # Create log file to store timings and surface mesh data
    output = args.output_dir
    if output is None:
        log_file = os.path.join('log.txt')
    else:
        log_file = os.path.join(output,'log.txt')
    if not(os.path.isfile(log_file)):
        with open(log_file,'w') as f:
            f.write(f'# Log file for {input_dir} at {datetime.now()} \n')
            f.write(f'# Cell name | Mesh computation time (s) | number of vertices | number of faces | bad triangle ratio | minimum edge length| surface area | average_edge_length | enclosed volume\n')

    # Begin iterating through cells
    for file in files:
        # Extract cellname and set save location
        cellname = os.path.basename(file).replace('.swc','')
        if output is not None:
            output_file = os.path.join(output,cellname+".ply")
        else:
            output_file = os.path.join(input_dir,cellname+".ply")
        print(f'Meshing {cellname}')

        # If a surface mesh does not already exist, create one.
        if not(os.path.isfile(output_file)):
            start = time.time()

            # Create swc object and make mesh.            
            swc = Swc(os.path.join(input_dir,file),True,2.0,1.0)
            ms = swc.make_mesh(simplify=True,output_dir=output)
            
            # Store timings and mesh data into log file
            bad_triangle_ratio = get_bad_triangle_ratio(ms)
            minimum_edge = get_min_edge_length(ms)
            surface_area,mesh_volume,avg_edge_length = get_other_stats(ms)
            with open(log_file,'a') as f:
                f.write(f'{cellname} {time.time()-start:.2f} {ms.current_mesh().vertex_number()} {ms.current_mesh().face_number()} {bad_triangle_ratio} {minimum_edge} {surface_area} {avg_edge_length} {mesh_volume}\n')
        print(f'Completed {cellname}')

