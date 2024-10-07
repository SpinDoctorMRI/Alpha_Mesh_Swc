import pymeshlab as mlab
import numpy as np
from src import Swc
import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import time


def main(mesh,source,output,save_pc=False):
    start=time.time()
    ms = mlab.MeshSet()
    ms.load_new_mesh(mesh)
    ms.compute_selection_by_small_disconnected_components_per_face(nbfaceratio=0.99)
    ms.meshing_remove_selected_vertices_and_faces()
    # m,r_min=get_raw_point_cloud(source)
    # ms.add_mesh(m)
    # clean_point_cloud(ms,r_min) 
    swc = Swc(source,process=True,Delta=0.1,delta=0.05)
    ms_soma = mlab.MeshSet()
    ms_soma.load_new_mesh(source.replace('.swc','.wrl'))
    l = 2*np.sqrt(2)/ms_soma.get_geometric_measures()['surface_area']
    bbox = ms_soma.get_geometric_measures()['bbox']
    area = ms_soma.get_geometric_measures()['surface_area']
    swc.make_point_cloud(density = 20/area)

    ms_pc = swc.add_mesh_to_point_cloud(ms_soma,includemesh=True)
    bbox = ms_pc.get_geometric_measures()['bbox']

    ms_pc.meshing_merge_close_vertices(threshold= mlab.PercentageValue(50*l/bbox.diagonal()))



    ms.add_mesh(ms_pc.current_mesh())
    # dist = ms.get_hausdorff_distance(sampledmesh=0,targetmesh=1,sampleedge=True,sampleface=True)
    ms.compute_scalar_by_distance_from_another_mesh_per_vertex(measuremesh=1,refmesh=0,signeddist =False)
    d = ms.current_mesh().vertex_scalar_array()
    bbox_swc = ms.get_geometric_measures()['bbox']
    ms.set_current_mesh(0)
    bbox_mesh = ms.get_geometric_measures()['bbox']
    dist = {}
    dist['RMS'] = np.sqrt(np.mean(d**2))
    dist['max'] = np.max(d)
    dist['mean'] = np.mean(d)
    dist['min'] = np.min(d)
    dist['diag_swc'] = bbox_swc.diagonal()
    dist['diag_mesh'] = bbox_mesh.diagonal()

    print('Surface error information')
    for key in dist.keys():
        print(f'{key} : {dist[key]}')

    with open(output,'w') as f:
        for key in dist.keys():
            f.write(f'{key} : {dist[key]}\n')
    if save_pc:
        ms.set_current_mesh(1)
        ms.compute_color_from_scalar_per_vertex(colormap='Viridis')
        ms.save_current_mesh(pcname,binary=False)

        cbar_name=pcname.replace('_pc.ply','_cbar.png')
        cmap = mpl.cm.viridis
        norm = mpl.colors.Normalize(vmin=np.min(d), vmax=np.max(d))
        fig, ax = plt.subplots(figsize=(1, 6), layout='constrained')
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
             cax=ax, orientation='vertical', label='Local error')
        plt.savefig(cbar_name, format='png', bbox_inches='tight', dpi=100, transparent=True)
    print(f'Elapsed time = {time.time() -start:.2f} s')
        
if __name__=='__main__':
    '''Input mesh and swc to generate point cloud. The distance between the point cloud and the mesh is computed.
    Parameters:
        mesh_file (path)
        swc file (path)
        output file (path)
        save_pc (optional). If set to 1 then the point cloud is saved with the local mesh error. Used to create plots with view_point_cloud, get_point_cloud_image
                save_pc also saves a color bar to be used in plotting.
    '''
    mesh=sys.argv[1]
    source=sys.argv[2]
    output=sys.argv[3]
    save_pc = len(sys.argv) == 5
    if save_pc:
        pcname=output.replace('.txt','_pc.ply')
    
    main(mesh,source,output,save_pc)
    