from src import Swc
import numpy as np
import sys
import pymeshlab as mlab
import os
import warnings
warnings.filterwarnings("ignore")

def flip_branch(c0,new_source):
    c_copy = 0+ c0
    c_copy[new_source,1] = -1
    found_old_source= False
    node = new_source
    changed = [node]
    while not(found_old_source):
        new_node = c0[node,1]
        c_copy[new_node,1] =  node
        found_old_source = c0[new_node,1] == -1
        node =new_node
        changed.append(node)
    return c_copy

if __name__=='__main__':
    '''Used for meshing microglia from Imaris software, with separate skelton and soma files.
    Takes as input a swc file which shares directory with it's soma. 
    This file computes the centre of mass of the soma surface, and this is then inserted as a parent node 
    in the cleaned swc file.
    '''
    input_file = sys.argv[1]
    output_dir = sys.argv[2]
    swc = Swc(input_file,process=False)
    # swc = Swc(input_file,process=True,Delta= 0.5,delta=0.25)
    types = swc.type_data
    # ms,_,_ = swc.make_mesh(alpha_fraction=0.001)
    # ms.save_current_mesh('test.ply',binary=False)
    if types[0] !=1:
        p0 = swc.position_data
        r0 = swc.radius_data
        c0 = swc.conn_data
        t0 = swc.type_data
        ms = mlab.MeshSet()
        # ms.load_new_mesh(file.replace('.swc','.wrl'))
        # gm = ms.get_geometric_measures()
        # soma = gm['center_of_mass']
        
        # '''Reordering branches as necessary'''
        N_nodes = len(t0)
        branches = np.zeros(N_nodes)
        N_branches= 0
        classified_nodes = []
        for i in range(0,N_nodes):
            if c0[i,1] == -1:
                N_branches +=1
                classified_nodes.append(i)
                branches[i] = N_branches
            else:
                j = c0[i,1]
                while j not in classified_nodes:
                    j = c0[i,1]
                classified_nodes.append(i)
                branches[i] = branches[j]
        N_children = [sum(c0[:,1] == i) for i in range(0,N_nodes)]
        

        
        # p1 = np.vstack((soma,p0))
        # t1 = np.hstack((1,t0))
        # t1[t1 == -1] = 3
        # c1 = np.vstack((np.zeros(2),c0))
        # r1 = np.hstack((r0[0],r0))
        # # t1[t1 == -1] = 3
        # # c1[1:,:] = c0
        # # c1[c1[:,1] == 0,1] = 0
        # c1[0,1] = -1
        # c1[0,0] = 1

        for i in range(1,N_branches+1):
            ind = branches == i

            file =os.path.basename(input_file)
            file = file.replace('.','_')
            print(file)
            file = os.path.join(output_dir,file.replace('_swc',f'_{i}.swc'))
            data = []
            p1 = p0[ind]
            t1 = t0[ind]
            conn_data = c0[ind,:]
            source = conn_data[:,1] == -1
            inverse_map =[c0[i,0] for i in range(0,N_nodes) if ind[i]]
            c1 = conn_data + 0
            for j,x in enumerate(inverse_map):
                c1[conn_data[:,0] == x,0] = j +1
                c1[conn_data[:,1] == x,1] = j +1 
                
            r1 = r0[ind]
            t1[t1 == -1] = 1


            N = len(p1)
            
            for i in range(0,N):    
                entry = '{0} {1} {2} {3} {4} {5} {6} \n'.format(int(conn_data[i,0]),int(t1[i]),p1[i,0],p1[i,1],p1[i,2],r1[i],int(conn_data[i,1]))
                if t1[i] !=-2:
                    data.append(entry)
            with open(file, 'w') as f:
                f.writelines(swc.preamble)
                f.writelines(data)
            print(os.path.abspath(file))

        # swc = Swc(file,process=True,Delta= 0.5,delta=0.25)
        # swc.write(file,append_clean=False)
    else:    
        file =os.path.basename(input_file)
        file = os.path.join(output_dir,file)
        swc.file= file
        swc.write(append_clean=False)
    