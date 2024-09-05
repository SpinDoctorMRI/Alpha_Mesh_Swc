from src import Swc
import argparse
import time
import os
from mesh_swc import main
from get_mesh_stats import mesh_stats

        
           

# Takes as input a directory of swc files and produces surface meshes for each one.
if __name__ =='__main__':
    description = """Reads swc files from a directory and produces coarse watertight surface meshs"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", type = str,help="Input SWC directory.")
    parser.add_argument("--output_dir",help="Output directory for meshes")
    parser.add_argument("--alpha",type=float,default=None,help="Alpha fraction for alpha wrapping")
    parser.add_argument("--Delta",type=float,default=2.0,help= "Smoothing parameter for swc file.")

    parser.add_argument("--simplify",type=int,help="Flag to simplify mesh",default=1)
    parser.add_argument("--min_faces",type=int,help="Minimum faces for the mesh",default=None)
    parser.add_argument("--dfaces",type=int,help="Rate to increase target number of faces in mesh",default=None)
    parser.add_argument("--tetgen_args",type=str,help="Parameters to pass into TetGen",default=None)
    parser.add_argument("--store_data",type=int,default=1,help="Flag to store meshing data. Set to 0 to remove")
    parser.add_argument("--save_alpha_mesh",type=int,help="Flag to save alpha wrapping mesh",default=0)

    args = parser.parse_args()

    store_data = args.store_data == 1
    input_dir = args.input_dir
    output_dir = args.output_dir
    min_faces = args.min_faces
    alpha_fraction = args.alpha
    dfaces = args.dfaces
    tetgen_args = args.tetgen_args
    simplify= args.simplify ==1
    save_alpha_mesh= args.save_alpha_mesh ==1
    Delta = args.Delta

    files =[os.path.abspath(os.path.join(input_dir,file)) for file in  os.listdir(input_dir) if file.endswith('.swc')]
    output_dir = args.output_dir
    if not(os.path.isdir(output_dir)):
        print(f'Creating {output_dir}')
        os.mkdir(output_dir)
    # Begin iterating through cells
    for file in files:
        try:
            print(f'Meshing {file}')
            output_file = os.path.join(output_dir,os.path.basename(file).replace('.swc','.ply'))
            if not(os.path.isfile(output_file)):
                swc,timings,ms,mesh_name,ms_alpha = main(file,output_dir,alpha_fraction,min_faces,dfaces,simplify,Delta,tetgen_args,save_alpha_mesh)
                output_file = mesh_name
                if store_data:
                    print(mesh_name)
                    data = mesh_stats(swc,ms,ms_alpha,mesh_name)
                    with open(output_file.replace('.ply','_log.txt'),'w') as f:
                        for key in data.keys():
                            f.write(f'{key}:{data[key]}\n')
                    print(f"Saved data for {file}")
            else:
                print(f'{output_file} already exists, skipping {file}')
        except (RuntimeError,ValueError) as e:
            print(f'Error with {file}:\n {repr(e)}') 
            with open(f'{output_dir}/Failed_meshes.txt','a') as f:
                f.write(f'Error with {file}:\n {repr(e)}\n')
        swc =None
        timings=None
        ms=None
        mesh_name=None
        ms_alpha= None
        data = None 