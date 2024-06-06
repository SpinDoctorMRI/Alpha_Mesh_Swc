from src import Swc
import argparse
import time
import os

if __name__ =='__main__':
    description = """Reads swc file and produces a coarse watertight surface mesh"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="Input SWC file.")
    parser.add_argument("--output_dir",help="Output directory for mesh")
    parser.add_argument("--min_faces",help="Minimum faces for the mesh")
    args = parser.parse_args()
    file = args.file
    output = args.output_dir
    min_faces = args.min_faces

    start = time.time()
    swc = Swc(file,True,2.0,1.0)
    swc.write()
    swc.make_mesh(simplify=True,output_dir=output,min_faces=min_faces)
    print(f'Total Elapsed time = {time.time()-start:.2f}')


