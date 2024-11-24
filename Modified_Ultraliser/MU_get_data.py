import os
import numpy as np
import sqlite3
import pandas as pd   
import argparse
import pymeshlab as mlab


def read_log_file(log_file):

    time_entries=[]
    with open(log_file,'r') as f:
        for line in f:
            if line[0:4] == 'real':
                time_entries.append(line)
    if len(time_entries)  < 4:
        print('Not finished')
        return 0 , 0 , 0 ,0
    soma_data = time_entries[0].replace('real	','').split('m')
    skeleton_data =  time_entries[1].replace('real	','').split('m')
    merging_data =  time_entries[2].replace('real	','').split('m')
    simplify_data =  time_entries[3].replace('real	','').split('m')
    soma_time = 60*float(soma_data[0]) + float(soma_data[1].replace('s\n',''))
    skeleton_time = 60*float(skeleton_data[0]) + float(skeleton_data[1].replace('s\n',''))    
    merging_time = 60*float(merging_data[0]) + float(merging_data[1].replace('s\n',''))    
    simplify_time = 60*float(simplify_data[0]) + float(simplify_data[1].replace('s\n',''))   
    return soma_time,skeleton_time,merging_time,simplify_time

if __name__=='__main__':
    description='''Search through meshes produced by modified Ultraliser, recording meshing times and surface sizes.'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", type = str,help="Input directory.")
    parser.add_argument("output", type = str,help="Output summary file.")
    parser.add_argument("--SME_dir", type = str,help="Input directory of SME files.", default=None)
    
    args = parser.parse_args()

    input_dir = args.input_dir
    output=args.output
    SME_dir = args.SME_dir

    mesh_files=[os.path.abspath(os.path.join(input_dir,file)) for file in os.listdir(input_dir) if file.endswith('.ply')]
    log_files=[os.path.abspath(os.path.join(input_dir,file)) for file in os.listdir(input_dir) if file.endswith('_log.txt')]
    
    data = []
    ms = mlab.MeshSet()
    for mesh in mesh_files:
        cell_data = {}
        # Get cell name
        cell_data['morphology'] = os.path.basename(mesh).replace('.ply','')
        # Get Mesh data
        ms.load_new_mesh(mesh)
        cell_data['vertex_number'] = ms.current_mesh().vertex_number()
        cell_data['face_number'] = ms.current_mesh().face_number()
        gm = ms.get_geometric_measures()
        cell_data['volume'] = gm['mesh_volume']
        cell_data['surface_area'] = gm['surface_area']
        ms.clear()

        # Get timing data
        log_file=mesh.replace('.ply','_log.txt')
        # with open(log_file,'r') as f:
        #     log_file_data = f.readlines()
        # soma_data = log_file_data[3].replace('real	','').split('m')
        # skeleton_data =  log_file_data[8].replace('real	','').split('m')
        # merging_data =  log_file_data[13].replace('real	','').split('m')
        # simplify_data =  log_file_data[18].replace('real	','').split('m')
        
        # soma_time = 60*float(soma_data[0]) + float(soma_data[1].replace('s\n',''))
        # skeleton_time = 60*float(skeleton_data[0]) + float(skeleton_data[1].replace('s\n',''))    
        # merging_time = 60*float(merging_data[0]) + float(merging_data[1].replace('s\n',''))    
        # simplify_time = 60*float(simplify_data[0]) + float(simplify_data[1].replace('s\n',''))    
        soma_time,skeleton_time,merging_time,simplify_time = read_log_file(log_file)
        cell_data['soma_time'] = soma_time
        cell_data['skeleton_time'] = skeleton_time
        cell_data['merging_time'] = merging_time
        cell_data['simplify_time'] = simplify_time
        cell_data['total_time'] = soma_time + skeleton_time + merging_time + simplify_time
        

        
        if SME_dir is not None:
            SME_file = os.path.join(SME_dir,cell_data['morphology']+'.txt')
            if os.path.isfile(SME_file):
                with open(SME_file,'r') as f:
                    SME_data = f.readlines()
                SME = float(SME_data[0].replace('RMS : ',''))
            else:
                SME = -1
        else:
            SME = -1

        cell_data['SME'] = SME
        print(cell_data)

        data.append(cell_data)

    data = pd.DataFrame(data)
    conn = sqlite3.connect(output)
    data.to_sql('Modified_Ultraliser',conn,if_exists='replace')

    print(f'{len(mesh_files)} produced out of {len(log_files)} inputs.')