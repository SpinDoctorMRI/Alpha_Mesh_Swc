import os
from sys import platform
import warnings
import numpy as np
from pathlib import Path

def call_tetgen(file,args='-d'):
    pytetgen_path =  Path(__file__)
    tetgen_base_path = os.path.dirname(pytetgen_path)

    if platform == 'win32':
        tetgen_cmd = f'{tetgen_base_path}/tetgen/win64/tetgen'
    elif platform =='darwin':
        cwd = os.getcwd()
        tetgen_cmd = f'mv {file} {tetgen_base_path}/tetgen/mac64/{os.path.basename(file)};\ncd {tetgen_base_path}/tetgen/mac64;\ntetgen'
    elif platform == "linux" or platform == "linux2":
        cwd = os.getcwd()
        tetgen_cmd = f'mv {file} {tetgen_base_path}/tetgen/lin64/{os.path.basename(file)};\ncd {tetgen_base_path}/tetgen/lin64;\ntetgen.exe'
    else:
        msg = f'{platform} not supported for TetGen use\nTrying linux command'
        warnings.warn(msg)
        tetgen_cmd = f'{tetgen_base_path}/tetgen/lin64/tetgen'
    if platform !='linux' and platform !='linux2' and platform !='darwin':
        print(f'{tetgen_cmd} {args} {file}')
        output = os.popen(f'{tetgen_cmd} {args} {file}').read()
    else:
        # print(f'{tetgen_cmd} {args} {file}; cd {cwd}')
        Move_command = f'mv {os.path.splitext(os.path.basename(file))[0]}.* {os.path.dirname(file)}/'
        print(f'{tetgen_cmd} {args} {os.path.basename(file)};\n{Move_command};\ncd {cwd};')
        output = os.popen(f'{tetgen_cmd} {args} {os.path.basename(file)};\n{Move_command};\ncd {cwd};').read()
    print(output)
    print('TetGen call completed')
    return output

def read_tetgen(tet_file):
    with open(tet_file+'.node','r') as f:
        nodes = np.loadtxt(f,skiprows=1,usecols=(1,2,3))
    with open(tet_file+'.ele','r') as f:
        elements = np.loadtxt(f,skiprows=1,usecols=(1,2,3,4),dtype=int)
    return nodes, elements