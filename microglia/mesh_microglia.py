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
    parser.add_argument("--min_faces",help="Minimum faces for the mesh")
    args = parser.parse_args()
    dendrite_file = '.'.join([args.name.replace('\r',''),'swc'])
    cellname = os.path.basename(dendrite_file)
    output = os.path.join(args.output_dir,cellname.replace('.swc','.ply'))
    min_faces = args.min_faces
    
    # Create mesh for processes
    print(f'Loading {dendrite_file}')
    start = time.time()
    swc = Swc(dendrite_file,process=True,Delta=1.0,delta=0.1)
    r_min = min(swc.radius_data)
    total_length = swc.get_length()
    dfaces = int(total_length*4)
    if min_faces is None or int(min_faces)<dfaces:
        min_faces = dfaces
    else:
        min_faces = int(min_faces)
    
    # Manually set alpha_fraction
    alpha_fraction = 0.0025
    ms_dendrites = swc.make_mesh(simplify=False,alpha_fraction= alpha_fraction,save=False)


    # Load soma mesh
    ms = mlab.MeshSet()
    # ms.load_new_mesh('_'.join([args.name.replace('\r',''),'soma.ply']))
    ms.load_new_mesh('.'.join([args.name.replace('\r',''),'wrl']))
    ms_soma = mlab.MeshSet()

    # Merge meshes and apply alpha wrap
    ms_soma.add_mesh(ms.current_mesh())
    ms_soma.generate_alpha_wrap(alpha_fraction=alpha_fraction,offset_fraction=alpha_fraction/30)
    
    # Simplify mesh
    ms_soma = simplify_mesh(ms_soma,dfaces/3,r_min,min_faces/3)

    # Save Soma mesh
    ms_soma.save_current_mesh(output.replace('.ply','_soma.ply'),binary=False)

    # Save separate process mesh
    m = ms_dendrites.current_mesh()
    ms.add_mesh(m)
    ms.generate_by_merging_visible_meshes()
    ms_dendrites.generate_splitting_by_connected_components(delete_source_mesh=True)
    for i in range(0,ms_dendrites.mesh_number()-1):
        ms_d = mlab.MeshSet()
        m = ms_dendrites.current_mesh()
        ms_d.add_mesh(m)
        ms_d = simplify_mesh(ms_d,dfaces/3,r_min,min_faces/3)
        ms_d.save_current_mesh(output.replace('.ply',f'_process_{i+1}.ply'),binary=False)
        ms_dendrites.delete_current_mesh()


    # ms.save_current_mesh('merged_mesh.ply',binary = False)
    # r_min = min(swc.radius_data)
    # gm = ms.get_geometric_measures()
    # bbox = gm['bbox']
    # # alpha_fraction = r_min/bbox.diagonal()
    # print(f'alpha_fraction = {alpha_fraction}')
    # ms.generate_alpha_wrap(alpha_fraction = alpha_fraction,offset_fraction =alpha_fraction/30)
    # total_length = swc.get_length()
    # dfaces = int(total_length*4)
    # if min_faces is None or int(min_faces)<dfaces:
    #     min_faces = dfaces
    # else:
    #     min_faces = int(min_faces)
    # print(f'min_faces = {min_faces}, dfaces = {dfaces}')
    # ms = simplify_mesh(ms,dfaces,r_min,min_faces)
    
    # # ms.save_current_mesh(output ,binary=False)
    print(f'Total Elapsed time = {time.time()-start:.2f}')
    print(f'Saved to {output}')