from src import Swc
import argparse
import time
import os
# import pandas as pd
# import sqlite3

# from joblib import Parallel, delayed
from get_mesh_stats import mesh_stats
import glob
def unit(file):
    # Extract cellname and set save location
    cellname = os.path.basename(file).replace('.swc','')
    if output_dir is not None:
        output_file = os.path.join(output_dir,cellname+".ply")
    else:
        output_file = os.path.join(input_dir,cellname+".ply")

    print(f'Meshing {cellname}')
    # If a surface mesh does not already exist, create one.
    failed_file =os.path.join(os.path.dirname(output_file),'failed_meshes',os.path.basename(output_file))
    if not(os.path.isfile(output_file)) and not(os.path.isfile(failed_file)):
        start = time.time()
        try:
            # Create swc object and make mesh.            
            swc = Swc(os.path.join(file),True,2.0,1.0)
            ms,mesh_name,ms_alpha = swc.make_mesh(simplify=True,output_dir=output_dir,save_alpha_mesh=False)
            print(f'Completed {cellname}, Elapsed time = {time.time() - start}')
            if store_data:
                print(mesh_name)
                data = mesh_stats(swc,ms,ms_alpha,mesh_name)
                # Store data
                # conn = sqlite3.connect(log_file)
                # data = pd.DataFrame(data)
                # data.to_sql('meshing_stats',conn,if_exists="append",index=False)
                with open(output_file.replace('.ply','_log.txt'),'w') as f:
                    for key in data.keys():
                        f.write(f'{key}:{data[key]}\n')
                    
                print(f"Saved data for {cellname}")
        except Exception as e:
            print(f'Error with {cellname}:\n {repr(e)}') 
            if os.path.isfile(output_file):
                if not(os.path.isdir(f'{output_dir}/failed_meshes')):
                    print(f'Creating {output_dir}/failed_meshes')
                    os.mkdir(f'{output_dir}/failed_meshes')
                os.rename(output_file,failed_file )
            # Add in log file.
            with open(f'{output_dir}/Failed_meshes.txt','a') as f:
                f.write(f'{cellname}\n')

# Takes as input a directory of swc files and produces surface meshes for each one.
if __name__ =='__main__':
    description = """Reads swc files from a directory and produces coarse watertight surface meshs"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", help="Input SWC directory.")
    parser.add_argument("--output_dir",help="Output directory for meshes")
    parser.add_argument("--store_data",type=bool,default=True,help="Flag to store meshing data")
    args = parser.parse_args()

    store_data = args.store_data

    # Find input swc files
    input_dir = str(args.input_dir)


    files =[file for file in  os.listdir(input_dir) if file.endswith('.swc')]
    # files = glob.glob(f'{input_dir}/*/*/*.swc')
    # files.reverse()
    # files = [os.path.basename(file) for file in files]
    # Find output directory
    output_dir = args.output_dir
    if not(os.path.isdir(output_dir)):
        print(f'Creating {output_dir}')
        os.mkdir(output_dir)

    # Create log file to store information
    if output_dir is None and store_data:
        log_file = os.path.join('mesh_stats.db')
    else:
        log_file = os.path.join(output_dir,'mesh_stats.db')

    
    # Begin iterating through cells
    for file in files:
        # Parallel(n_jobs=10)(delayed(mesh_cell(file)) for file in files)
        unit(f'{input_dir}/{file}')
    