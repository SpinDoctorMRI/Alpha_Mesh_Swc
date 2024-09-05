from src import simplify_mesh
import pymeshlab as mlab
import os
import time
import sys
from os.path import join,abspath,basename,isfile

if __name__=='__main__':
    '''Apply simplification proceedure to an input directory of meshes.
    Custom simplification parameters should be adjusted here.'''
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    files = [abspath(join(input_dir,file)) for file in os.listdir(input_dir) if file.endswith(".ply")]

    ms = mlab.MeshSet()
    nfiles = len(files)
    for i,file in enumerate(files):
        print(f'Processing {i}/{nfiles}')
        filename= basename(file)
        output_file = join(output_dir,filename)
        if not(isfile(output_file)):        
            start  = time.time()
            ms.load_new_mesh(file)
            start_vertices = ms.current_mesh().vertex_number()

            log_file = join(output_dir,filename.replace('.ply','_log.txt'))
            # Using default hard-coded parameters.
            ms = simplify_mesh(ms,temp_dir_name=output_file.replace('.ply','')) 
            # Using custom simplification parameters here.
            # ms = simplify_mesh(ms,dfaces=1000,r_min=0.1,min_faces=2000,temp_dir_name=output_file.replace('.ply',''))
            
            print(f"Elapsed time = {time.time() - start:.1f}")
            with open(log_file,'w') as f:
                f.write(f"Old_vertices:{start_vertices}\nNew_vertices:{ms.current_mesh().vertex_number()}\nTime:{time.time() - start}")
            ms.save_current_mesh(output_file,binary=False)
            ms.clear()