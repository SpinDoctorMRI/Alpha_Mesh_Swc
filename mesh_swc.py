from src import Swc
import argparse
import time
from src.pytetgen import call_tetgen

if __name__ =='__main__':
    description = """Reads swc file and produces a coarse watertight surface mesh"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="Input SWC file.")
    parser.add_argument("--output_dir",help="Output directory for mesh")
    parser.add_argument("--alpha",type=float,default=None,help="Alpha fraction for alpha wrapping")
    parser.add_argument("--Delta",type=float,default=2.0,help= "Smoothing parameter for swc file.")

    parser.add_argument("--simplify",type=int,help="Flag to simplify mesh",default=1)
    parser.add_argument("--min_faces",type=int,help="Minimum faces for the mesh",default=None)
    parser.add_argument("--dfaces",type=int,help="Rate to increase target number of faces in mesh",default=None)
    parser.add_argument("--tetgen",type=str,help="Parameters to pass into TetGen",default=None)

    args = parser.parse_args()

    file = args.file
    output_dir = args.output_dir
    min_faces = args.min_faces
    alpha_fraction = args.alpha
    start = time.time()
    swc = Swc(file,True,args.Delta,args.Delta/2)
    swc.write()
    ms,mesh_name,_ = swc.make_mesh(simplify=(args.simplify == 1),output_dir=output_dir,min_faces=min_faces,alpha_fraction=alpha_fraction)
    timings = swc.timings

    if args.tetgen is not None:
        tetgen_args = args.tetgen
        start_tet = time.time()
        call_tetgen(mesh_name,tetgen_args)
        timings['tetgen'] = time.time() - start_tet

    print(f'Total Elapsed time = {time.time()-start:.2f}')
    print('Individual timings:')
    print(swc.timings)