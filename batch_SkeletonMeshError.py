import argparse
import os
from SkeletonMeshError import main
import sqlite3
import pandas as pd

def parse_data(file):
    data = {'mesh':file}
    with open(file,'r') as f:
        for line in f:
            key,value = line.split(':')
            value = value.replace('\n','')
            key = key.replace(' ','')
            data[key] = float(value)
    return data
def gather_data(direc):
    files = os.listdir(direc)
    data = []
    for file in files:
        if not(file.endswith('.db')):
            data.append(parse_data(os.path.join(direc,file)))

    data = pd.DataFrame(data)
    conn=sqlite3.connect(os.path.join(direc,'summary.db'))
    data.to_sql('summary',conn,if_exists="replace",index=False)
    return data

def read_gathered_data(direc):
    conn=sqlite3.connect(os.path.join(direc,'summary.db'))
    data= pd.read_sql_query('SELECT * FROM summary',conn)
    return data


if __name__=='__main__':
    description=''' Compute the Skeleton to Mesh error for all meshes in a directory'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("mesh_dir", help="Input mesh directory.")
    parser.add_argument("source_dir", help="Input SWC directory.")
    parser.add_argument("output_dir", help="Output text directory.")
    parser.add_argument("--save_pc",help="Optional flag to save point cloud distances",default=0,type=int)
    parser.add_argument("--remove_suffix",help="Suffix added to mesh file which is not present in swc file",default='')
    parser.add_argument("--add_suffix",help="Suffix removed from mesh file which is present in swc file",default='')
    
    args = parser.parse_args()
    direc = args.mesh_dir
    swc_direc = args.source_dir
    output_direc=args.output_dir
    save_pc = args.save_pc ==1
    remove_suffix=args.remove_suffix
    add_suffix=args.add_suffix
    if not(os.path.isdir(output_direc)):
        os.mkdir(output_direc)

    files = [file for file in os.listdir(direc) if file.endswith('.ply') or file.endswith('.obj')]
    for file in files:
        mesh= f'{direc}/{file}'
        if file.endswith('.ply'):
            ext = '.ply'
        if file.endswith('.obj'):
            ext = '.obj'
        source=file.replace(f'{remove_suffix}{ext}',f'{add_suffix}.swc')
        source=f'{swc_direc}/{source}'
        output=file.replace(ext,'.txt')
        output=f'{output_direc}/{output}'
        try:
            if os.path.isfile(output):
                print(f'{file} already completed')
            else:
                print(mesh)
                main(mesh,source,output,save_pc)
        except:
            print(f'Error with {file}')

    summary_file=os.path.join(output_direc,'summary.db')
    print(f'Analysis complete, creating summary in {summary_file}')
    gather_data(output_direc)