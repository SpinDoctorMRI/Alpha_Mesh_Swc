from src import Swc
import argparse
import time
from src.pytetgen import call_tetgen


def main(file,output_dir,alpha_fraction,min_faces,dfaces,simplify,Delta,tetgen_args,save_alpha_mesh):
    start = time.time()

    swc = Swc(file,True,Delta,Delta/2)

    # swc.write() # store clean swc file
    ms,mesh_name,ms_alpha = swc.make_mesh(simplify,output_dir=output_dir,min_faces=min_faces,dfaces=dfaces,alpha_fraction=alpha_fraction,save_alpha_mesh=save_alpha_mesh)
    timings = swc.timings

    if tetgen_args is not None:
        start_tet = time.time()
        call_tetgen(mesh_name,tetgen_args)
        timings['tetgen'] = time.time() - start_tet

    print(f'Completed {mesh_name}.\nTotal Elapsed time = {time.time()-start:.2f}')
    # print('Individual timings:')
    # print(swc.timings)
    return swc,timings,ms,mesh_name,ms_alpha

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
    parser.add_argument("--tetgen_args",type=str,help="Parameters to pass into TetGen",default=None)
    parser.add_argument("--save_alpha_mesh",type=int,help="Flag to save alpha wrapping mesh",default=0)
    args = parser.parse_args()

    file = args.file
    output_dir = args.output_dir
    min_faces = args.min_faces
    alpha_fraction = args.alpha
    dfaces = args.dfaces
    tetgen_args = args.tetgen_args
    simplify= args.simplify ==1
    save_alpha_mesh= args.save_alpha_mesh ==1
    Delta = args.Delta
    swc,timings,ms,mesh_name,ms_alpha = main(file,output_dir,alpha_fraction,min_faces,dfaces,simplify,Delta,tetgen_args,save_alpha_mesh)