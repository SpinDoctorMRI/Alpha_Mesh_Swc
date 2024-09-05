import os
from src import call_tetgen,read_tetgen
import sys
import numpy as np
import time
from get_mesh_stats import find_mesh_quality

def main(file,output,ext='.ply'):
    start = time.time()
    tet_output = call_tetgen(file,'-pq1.2a1.0O9VCBF')
    tetgen_time=time.time()-start
    print(tet_output)
    tet_file = file.replace(ext,'.1')
    mesh_quality,mesh_size = find_mesh_quality(tet_file)
    
    with open(output,'w') as f:
        f.write(f'femesh_size:{mesh_size}\nfemesh_quality:{mesh_quality}\ntetgen:{tetgen_time}')
    print(f'Removing tetgen files {tet_file}')
    for ext in ['.node','.ele','.smesh']:
        os.remove(tet_file+ext)

if __name__=='__main__':
    file = sys.argv[1]
    output = sys.argv[2]
    main(file,output)    
