from src import Swc,simplify_mesh
import argparse
import time
import os
import pymeshlab as mlab

if __name__ =='__main__':
    description = """Reads swc file and separate soma file and produces a coarse watertight surface mesh"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("name", help="Input name of cell.")
    parser.add_argument("--output_dir",help="Output directory for mesh",default='')
    parser.add_argument("--alpha",help=" Alpha fraction for alpha wrapping",type=float,default=0.0025)
    parser.add_argument("--simplify",type=int,help="Flag to simplify mesh",default=1)    
    parser.add_argument("--Delta",type=float,default=0.05,help= "Smoothing parameter for skeleton of swc file.")
    
    parser.add_argument("--min_faces",help="Minimum faces for the mesh")
    parser.add_argument("--segment_meshes",type = int,help="Flag to mesh separate segments",default=0)
    parser.add_argument("--soma_ext",help="Extension of soma file",default='.wrl')
    
    args = parser.parse_args()
    dendrite_file = '.'.join([args.name.replace('\r',''),'swc'])
    cellname = os.path.basename(dendrite_file)
    output = os.path.join(args.output_dir,cellname.replace('.swc','.ply'))
    min_faces = args.min_faces
    
    # Create mesh for processes
    print(f'Loading {dendrite_file}')
    start = time.time()
    swc = Swc(dendrite_file,process=True,Delta=args.Delta,delta=args.Delta/2)
    # Store simplification parameters if needed
    if args.simplify == 1:
        r_min = min(swc.radius_data)
        total_length = swc.get_length()
        dfaces = int(total_length*4)
        if min_faces is None:
            min_faces = dfaces
        else:
            min_faces = int(min_faces)


    # Manually set alpha_fraction
    alpha_fraction = args.alpha
    temp_dir_name = output.replace('.ply','')
    print(f'segment_meshes={args.segment_meshes}')
    if args.segment_meshes != 1:
        # Only mesh full surface
        ms = mlab.MeshSet()
        ms_dendrites = swc._build_initial_mesh()
        ms.add_mesh(ms_dendrites.current_mesh())
        ms.load_new_mesh(''.join([args.name.replace('\r',''),args.soma_ext]))
        ms.generate_by_merging_visible_meshes()
        ms.generate_alpha_wrap(alpha_fraction=alpha_fraction,offset_fraction=alpha_fraction/30)
        if args.simplify == 1:
            ms = simplify_mesh(ms,dfaces,r_min,min_faces,temp_dir_name=temp_dir_name)
        ms.save_current_mesh(output,binary=False)
        print(f'Saved to {output}')
    else:
        # Get separete dendrite and soma meshes
        ms_dendrites,_,_ = swc.make_mesh(simplify=False,alpha_fraction= alpha_fraction,save=False)
        ms_dendrites.generate_splitting_by_connected_components(delete_source_mesh=True)
        for i in range(0,ms_dendrites.mesh_number()-1):
            ms_d = mlab.MeshSet()
            m = ms_dendrites.current_mesh()
            ms_d.add_mesh(m)
            if args.simplify == 1:
                ms_d = simplify_mesh(ms_d,dfaces/3,r_min,min_faces/3,temp_dir_name=temp_dir_name)
            ms_d.save_current_mesh(output.replace('.ply',f'_process_{i+1}.ply'),binary=False)
            ms_dendrites.delete_current_mesh()
            print('Saved to '+output.replace('.ply',f'_process_{i+1}.ply'))

        # Load soma mesh
        ms_soma = mlab.MeshSet()
        ms_soma.load_new_mesh(''.join([args.name.replace('\r',''),args.soma_ext])) # or wrl
        # Apply alpha wrap
        ms_soma.generate_alpha_wrap(alpha_fraction=alpha_fraction,offset_fraction=alpha_fraction/30)
        # Simplify mesh
        if args.simplify == 1:
            ms_soma = simplify_mesh(ms_soma,dfaces/3,r_min,min_faces/3,temp_dir_name=temp_dir_name)

        ms_soma.save_current_mesh(output.replace('.ply','_soma.ply'),binary=False)
        print(f'Saved to' + output.replace('.ply','_soma.ply'))

    print(f'Total Elapsed time = {time.time()-start:.2f}')
