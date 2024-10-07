from src import simplify_mesh,is_watertight
import pymeshlab as mlab
import os
import time
import sys
from os.path import join,abspath,basename,isfile
import warnings
from src import Swc
if __name__=='__main__':
    '''Apply simplification proceedure to an input directory of meshes.
    Custom simplification parameters should be adjusted here.'''
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    source_dir = sys.argv[3]
    files = [abspath(join(input_dir,file)) for file in os.listdir(input_dir) if file.endswith(".ply")]

    if not(os.path.isdir(output_dir)):
        os.mkdir(output_dir)
    ms = mlab.MeshSet()
    nfiles = len(files)
    # files.reverse()
    import random
    random.shuffle(files)
    for i,file in enumerate(files):
        print(f'Processing {i+1}/{nfiles}')
        filename= basename(file)
        log_file = join(output_dir,filename.replace('.ply','_log.txt'))

        output_file = join(output_dir,filename)
        if not(isfile(output_file)) and not(isfile(log_file)):        
            start  = time.time()
            ms.load_new_mesh(file)
            start_vertices = ms.current_mesh().vertex_number()

            if is_watertight(ms,name=file.replace('.ply','')):
                swc = Swc(join(source_dir,filename.replace('.ply','.swc')))
                length = swc.get_length()
                dfaces  =int(8*length)
                min_faces = 2000
                # Using default hard-coded parameter    s.
                # ms = simplify_mesh(ms,temp_dir_name=output_file.replace('.ply','')) 
                # Using custom simplification parameters here.
                ms = simplify_mesh(ms,dfaces=dfaces,r_min=0.5,min_faces=min_faces,temp_dir_name=output_file.replace('.ply',''))
                print(f"Elapsed time = {time.time() - start:.1f}")
                with open(log_file,'w') as f:
                    f.write(f"Old_vertices:{start_vertices}\nNew_vertices:{ms.current_mesh().vertex_number()}\nTime:{time.time() - start}")
                ms.save_current_mesh(output_file,binary=False)
            else:
                msg = f'{file} is not a valid watertight mesh'
                warnings.warn(msg)
                with open(log_file,'w') as f:
                    f.write(msg)
            ms.clear()
            