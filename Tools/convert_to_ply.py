import pymeshlab as mlab
import sys
import os


if __name__=='__main__':
    '''Convert a surface mesh to ply format'''
    direc = sys.argv[1]
    output_dir = sys.argv[2]
    ms = mlab.MeshSet()
    files = os.listdir(direc)
    for file in files:
        try:
            ms.load_new_mesh(os.path.join(direc,file))
            filename, file_extension = os.path.splitext(file)
            output = os.path.join(output_dir,filename+'.ply')
            ms.save_current_mesh(output,binary=False)
            print(f'Converted {file}')
        except:
            print(f'Error with {file}')
        ms.clear()