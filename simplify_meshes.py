from src import simplify_mesh,is_watertight
import pymeshlab as mlab
import os
import time
from os.path import join,abspath,basename,isfile
import warnings
from src import Swc
import argparse
if __name__=='__main__':
    description='''Apply simplification proceedure to an input directory of meshes.
    Custom simplification parameters should be adjusted here.'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_dir", help="Input mesh directory.")
    parser.add_argument("source_dir", help="Input SWC directory.")
    parser.add_argument("output_dir", help="Output simplified mesh files.")
    args = parser.parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    source_dir = args.source_dir
    files = [abspath(join(input_dir,file)) for file in os.listdir(input_dir) if file.endswith(".ply")]

    if not(os.path.isdir(output_dir)):
        os.mkdir(output_dir)
    ms = mlab.MeshSet()
    nfiles = len(files)
    # files.reverse()
    # import random
    # random.shuffle(files)
    for i,file in enumerate(files):
        print(f'Processing {i+1}/{nfiles}')
        filename= basename(file)
        log_file = join(output_dir,filename.replace('.ply','_simp_log.txt'))

        output_file = join(output_dir,filename)
        if not(isfile(output_file)):        
            start  = time.time()
            ms.load_new_mesh(file)
            start_vertices = ms.current_mesh().vertex_number()

            if is_watertight(ms,name=file.replace('.ply','')):
                swc = Swc(join(source_dir,filename.replace('.ply','.swc')))
                total_length = swc.get_length()
                dfaces = int(total_length*8)
                min_faces = int(total_length*2)
                r_min = max(min(swc.radius_data),0.05)

                # Using default hard-coded parameter    s.
                # ms = simplify_mesh(ms,temp_dir_name=output_file.replace('.ply','')) 
                # Using custom simplification parameters here.
                ms = simplify_mesh(ms,dfaces=dfaces,r_min=r_min,min_faces=min_faces,temp_dir_name=output_file.replace('.ply',''))
                
                print(f"Elapsed time = {time.time() - start:.1f}")
                if ms.current_mesh().vertex_number() < start_vertices:
                    with open(log_file,'w') as f:
                        f.write(f"Old_vertices:{start_vertices}\nNew_vertices:{ms.current_mesh().vertex_number()}\nTime:{time.time() - start}")
                    
                    ms.save_current_mesh(output_file,binary=False)
                else:
                    print(f"ERROR\n\n\nOld_vertices:{start_vertices}\nNew_vertices:{ms.current_mesh().vertex_number()}")
            else:
                msg = f'{file} is not a valid watertight mesh'
                warnings.warn(msg)
                with open(log_file,'w') as f:
                    f.write(msg)
            ms.clear()
            