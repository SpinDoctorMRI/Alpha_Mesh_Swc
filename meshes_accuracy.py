import sys
import os
from mesh_accuracy import main
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
    direc = sys.argv[1]
    swc_direc = sys.argv[2]
    output_direc=sys.argv[3]
    if len(sys.argv) >=5:
        remove_suffix = sys.argv[4]
    else:
        remove_suffix = ''
    if len(sys.argv) == 6:
        add_suffix = sys.argv[5]
    else:
        add_suffix = ''
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
                main(mesh,source,output)
        except:
            print(f'Error with {file}')

    summary_file=os.path.join(output_direc,'summary.db')
    print(f'Analysis complete, creating summary in {summary_file}')
    gather_data(output_direc)