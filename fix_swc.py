from alphaSwc.src import Swc
import numpy as np
import sys
import pymeshlab as mlab
import os
import warnings
warnings.filterwarnings("ignore")


if __name__=='__main__':
    '''Used for meshing microglia from Imaris software, with separate skelton and soma files.
    Takes as input a swc file which shares directory with it's soma. 
    This file computes the centre of mass of the soma surface, and this is then inserted as a parent node 
    in the cleaned swc file.
    '''
    file = sys.argv[1]
    swc = Swc(file,process=False)
    types = swc.type_data
    # ms,_,_ = swc.make_mesh(alpha_fraction=0.001)
    # ms.save_current_mesh('test.ply',binary=False)
    if types[0] !=1:
        p0 = swc.position_data
        r0 = swc.radius_data
        c0 = swc.conn_data
        t0 = swc.type_data
        ms = mlab.MeshSet()
        ms.load_new_mesh(file.replace('.swc','.wrl'))
        gm = ms.get_geometric_measures()
        soma = gm['center_of_mass']
        p1 = np.vstack((soma,p0))
        t1 = np.hstack((1,t0))
        c1 = np.vstack((np.zeros(2),c0))
        r1 = np.hstack((r0[0],r0))
        t1[t1 == -1] = 3
        c1[1:,:] = c0 + 1
        c1[c1[:,1] == 0,1] = 0
        c1[0,1] = -1

        file = file.replace('.swc','_fixed.swc')
        data = []
        N = len(p1)
        conn_data= np.copy(c1)
        source_nodes = conn_data[:,1] == -1
        conn_data[:,0] = conn_data[:,0] + 1
        conn_data[~source_nodes,1] = conn_data[~source_nodes,1] + 1
        for i in range(0,N):    
            entry = '{0} {1} {2} {3} {4} {5} {6} \n'.format(int(conn_data[i,0]),int(t1[i]),p1[i,0],p1[i,1],p1[i,2],r1[i],int(conn_data[i,1]))
            data.append(entry)
        with open(file, 'w') as f:
            f.writelines(swc.preamble)
            f.writelines(data)
        print(os.path.abspath(file))

    else:
        swc.write()
        print(os.path.abspath(file.replace('.swc','_clean.swc')))
    