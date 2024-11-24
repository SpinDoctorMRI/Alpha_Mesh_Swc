import os
import sys
from check_femesh import main
import numpy as np
import sqlite3
import pandas as pd
import argparse
def parse_output(file):
    data = {}
    with open(file,'r') as f:
        for line in f:
            key,value = line.split(':')
            data[key] = float(value)
    return data

if __name__=='__main__':
    description = '''Call TetGen on meshed and store finite element mesh size and quality.'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", help="Input mesh directory.")
    parser.add_argument("output_dir", help="Output text directory.")
    parser.add_argument("summary_file", help="Output .db file.")
    args = parser.parse_args()

    input_dir =args.input_dir
    output_dir = args.output_dir
    summary_file = args.summary_file
    if not(os.path.isdir(output_dir)):
        os.mkdir(output_dir)
    files = [file for file in os.listdir(input_dir) if file.endswith('.ply')]
    nfiles= len(files)
    files.reverse()
    for i,file in enumerate(files):
        output = os.path.join(output_dir,file.replace('.ply','.txt'))
        if not(os.path.isfile(output)):
            try:
                main(os.path.join(input_dir,file),output)
            except Exception as e:
                print(e)
        else:
            print(f'{file} already meshed')
        print(f'Completed {i+1}/{nfiles}')

    outputs = os.listdir(output_dir)
    femesh_size=[]
    femesh_quality=[]
    femesh_time = []
    morphology = []
    for file in outputs:
        data = parse_output(os.path.join(output_dir,file))
        femesh_size.append(data['femesh_size'])
        femesh_quality.append(data['femesh_quality'])
        femesh_time.append(data['tetgen'])
        morphology = os.path.basename(file).replace('.txt','')

    femesh_size =np.array(femesh_size)
    femesh_quality =np.array(femesh_quality)
    femesh_time =np.array(femesh_time)

    conn =sqlite3.connect(summary_file)
    Data = pd.DataFrame({'morphology':morphology,'FE_vertices':femesh_size,
                        'FE_quality':femesh_quality,'FE_time': femesh_time})
    Data.to_sql('FE_data',conn,if_exists='replace')
    # np.save(os.path.join(summary_dir,'femesh_size.npy'),femesh_size)
    # np.save(os.path.join(summary_dir,'femesh_quality.npy'),femesh_quality)
    # np.save(os.path.join(summary_dir,'femesh_time.npy'),femesh_time)


