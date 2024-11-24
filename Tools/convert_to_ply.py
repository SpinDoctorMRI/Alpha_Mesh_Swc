import pymeshlab as mlab
import sys
import os


if __name__=='__main__':
    '''Convert a surface mesh to ply format'''
    input_file = sys.argv[1]
    output_name = sys.argv[2]
    ms = mlab.MeshSet()
    ms.load_new_mesh(input_file)
    filename, file_extension = os.path.splitext(os.path.basename(input_file))
    output = output_name + '.ply'
    ms.save_current_mesh(output,binary=False)
    print(f'Converted {input_file}')
    