import os
import sys
from check_femesh import main
import numpy as np
def parse_output(file):
    data = {}
    with open(file,'r') as f:
        for line in f:
            key,value = line.split(':')
            data[key] = float(value)
    return data

if __name__=='__main__':
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    summary_dir = sys.argv[3]
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
    for file in outputs:
        data = parse_output(os.path.join(output_dir,file))
        femesh_size.append(data['femesh_size'])
        femesh_quality.append(data['femesh_quality'])
        femesh_time.append(data['tetgen'])

    femesh_size =np.array(femesh_size)
    femesh_quality =np.array(femesh_quality)
    femesh_time =np.array(femesh_time)

    np.save(os.path.join(summary_dir,'femesh_size.npy'),femesh_size)
    np.save(os.path.join(summary_dir,'femesh_quality.npy'),femesh_quality)
    np.save(os.path.join(summary_dir,'femesh_time.npy'),femesh_time)


