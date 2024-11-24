import os
import numpy as np
import sqlite3
import pandas as pd   
import argparse
import pymeshlab as mlab

def remove_chars(value):
    for c  in ['\n','[',']']:
        value =value.replace(c,'')
    return value

types = {}
types['morphology'] = str
types['vertex_number'] = int
types['face_number'] = int
types['alpha_vertex_number'] = int
types['alpha_face_number'] = int
types['cleaned_swc_nodes'] = int
for key in ['surface_area','volume','alpha_surface_area','alpha_volume','extract_swc','reorder_swc',
            'process_swc','initialise_branches','initialising_individual_meshes','merging_individual_meshes',
            'alpha_wrap','simplify_mesh']:
    types[key] = float
for key in ['mesh_quality','tetgen']:
    types[key] = str



if __name__=='__main__':
    description='''Search through meshes produced by Alpha_Mesh_Swc, recording meshing times and surface sizes.'''
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
    for log in log_files:
        cell_data = {}
        
        # Get timings and mesh information
        with open(log,'r') as f:
            for line in f:
                key,values = line.split(':')
                cell_data[key] = types[key](remove_chars(values))
        
        # Get Skeleton Mesh Error
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

        cell_data['total_time'] = cell_data['extract_swc'] + cell_data['reorder_swc'] +cell_data['process_swc'] +cell_data['initialise_branches'] +cell_data['initialising_individual_meshes'] +cell_data['merging_individual_meshes'] +cell_data['alpha_wrap'] +cell_data['simplify_mesh']
        print(cell_data)

        data.append(cell_data)

    data = pd.DataFrame(data)
    conn = sqlite3.connect(output)
    data.to_sql('Alpha_Mesh_Swc',conn,if_exists='replace')

    print(f'{len(mesh_files)} produced out of {len(log_files)} inputs.')