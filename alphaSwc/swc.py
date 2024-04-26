import numpy as np
import warnings
from numpy.linalg import norm
import pymeshlab as mlab
from .tendril import Tendril
import os
from .mesh_processing import dcp_meshset,simplify_mesh


class Swc():
    '''Class to store and process nodes from swc data. This class stores the skeleton information we get from the swc files
    attributes:
        file
        position_data
        radius_data
        conn_data
        type_data
        premable: (string) text from beginning of swc file
        process: (bool) flag to denote whether to process swc
        Delta: (processing parameter) target average distance between nodes
        delta: (proccessing parameter) target average distance between nodes close to the soma
        branches: (array) stores the branch to which each node belongs.
        intersection_matrix: (sparse matrix) stores cross-branch intersections of nodes

    methods:
        write: write new processed data in swc format
        initialise_branches: finds branches of swc file.
        make_mesh: produce watertight surface mesh and save

    
    '''
    def __init__(self,
                 file= None,
                 process = False,
                 Delta = 2.0,
                 delta = 1.0
                 ):
        
        # Read file and check for correct ordering
        self.file = file
        position_data , radius_data, conn_data , type_data,preamble = extract_swc(self.file)
        position_data , radius_data, conn_data , type_data = reorder_swc(position_data,radius_data,conn_data,type_data)

        # Apply processing
        if process:
            position_data , radius_data, conn_data , type_data = smooth_swc( position_data , radius_data, conn_data , type_data,Delta)
            position_data , radius_data, conn_data , type_data = interpolate_swc( position_data , radius_data, conn_data , type_data,delta)

        # Store information
        self.position_data = position_data
        self.radius_data =radius_data
        self.type_data = type_data
        self.conn_data = conn_data
        self.process = process
        self.preamble = preamble
        # Compute branches
        self.initialise_branches()
        self.Delta = Delta

        return None
    def write(self):
        """Write the processed swc file in swc format"""

        file = self.file.replace('.swc','_clean.swc')
        data = []
        N = len(self.position_data)
        conn_data= np.copy(self.conn_data)
        conn_data[:,0] = conn_data[:,0] + 1
        conn_data[1:,1] = conn_data[1:,1] + 1
        for i in range(0,N):    
            entry = '{0} {1} {2} {3} {4} {5} {6} \n'.format(conn_data[i,0],self.type_data[i],self.position_data[i,0],self.position_data[i,1],self.position_data[i,2],self.radius_data[i],conn_data[i,1])
            data.append(entry)
        with open(file, 'w') as f:
            f.writelines(self.preamble)
            f.writelines(data)
        return file

    def initialise_branches(self):
        """"Creates branches along the neuron"""
        self.branches = create_branches(self.conn_data,self.type_data)
        return None

    def make_mesh(self,simplify=False,alpha_fraction= None,output_dir=None):
        """"Compute watertight surface mesh"""

        # Store output information
        if output_dir == None:
            name = self.file.replace('.swc','.ply')
        else:
            filename = os.path.basename(self.file)
            name = output_dir+'/'+filename.replace('.swc','.ply')
        
        # Get value for alpha_fraction
        if alpha_fraction == None:
            diag= get_bbox_diag(self.position_data)
            alpha_fraction = min(self.radius_data)/diag
        
        # Compute individual meshes

        ms = mlab.MeshSet()
        ms.create_sphere(radius = 1)
        v_S = ms.current_mesh().vertex_matrix()
        f_S = ms.current_mesh().face_matrix()
        b = self.branches
        p = self.position_data
        r = self.radius_data
        t = self.type_data
        c = self.conn_data
        N = len(r)
        ms = mlab.MeshSet()
        
        # Place spheres at somas
        for i in range(0,N):
            if t[i] == 1:    
                m = mlab.Mesh(vertex_matrix = p[i] + r[i]*v_S,face_matrix = f_S)
                ms.add_mesh(m)

        # Produce tubular meshes along branches
        branch_ids = np.unique(b)
        for branch in branch_ids:
            if branch >0:
                
                # Get relevent nodes for this branch
                nodes =np.where(b == branch)[0]
                nodes = np.hstack((c[nodes[0],1],nodes))
                n = np.where(c[:,1] == nodes[-1])[0]
                if len(n)>0:
                    nodes = np.hstack((nodes,n[0]))
                # Create tubular mesh
                tendril = Tendril(nodes,self,self.Delta)
                v,f= tendril.make_mesh(v_S,f_S)
                # Store mesh
                m = mlab.Mesh(vertex_matrix = v,face_matrix =f)
                ms.add_mesh(m)

        # Merge individual meshes 
        print(f'merging {ms.mesh_number()} meshes')
        ms.generate_by_merging_visible_meshes()

        # Apply alpha_wrap filter
        print(f'Applying alpha wrap to {self.file}')
        ms.generate_alpha_wrap(alpha_fraction = alpha_fraction,offset_fraction =alpha_fraction/30)
        # Begin simplification
        if simplify:
            attempt = 1
            flag = False
            edges = np.linalg.norm(p[c[c[:,1]>-1,0],:] - p[c[c[:,1]>-1,1],:],axis = 1)
            total_length = sum(edges)
            resolution_scale = int(total_length*4)
            ms_cp = dcp_meshset(ms)
            while not(flag) and attempt < 16:
                if attempt*resolution_scale > ms.current_mesh().face_number():
                    break
                print(f'Applying simplification, attempt = {attempt}')
                ms,flag = simplify_mesh(ms,attempt*resolution_scale)
                attempt+= 1
                if not(flag):
                    ms = dcp_meshset(ms_cp)


        print('Meshing complete')
        if flag:
            print('Meshing successful')
            print(f'Saving to {name}')
        else:
            print('Meshing failed, try with coarser alpha mesh')
            ms.generate_alpha_wrap(alpha_fraction = 5*alpha_fraction,offset_fraction =alpha_fraction/30)
            if simplify:
                attempt = 1
                flag = False
                edges = np.linalg.norm(p[c[c[:,1]>-1,0],:] - p[c[c[:,1]>-1,1],:],axis = 1)
                total_length = sum(edges)
                resolution_scale = int(total_length*4)
                ms_cp = dcp_meshset(ms)
                while not(flag) and attempt < 16:
                    if attempt*resolution_scale > ms.current_mesh().face_number():
                        break
                    print(f'Applying simplification, attempt = {attempt}')
                    ms,flag = simplify_mesh(ms,attempt*resolution_scale)
                    attempt+= 1
                    if not(flag):
                        ms = dcp_meshset(ms_cp)
        
        # Save mesh
        ms.save_current_mesh(name,binary=False)
        return ms


def get_bbox_diag(p):
    '''Returns diagonal of a bounding box for point cloud p'''
    min_x = min(p[:,0])
    min_y = min(p[:,1])
    min_z = min(p[:,2])
    max_x = max(p[:,0])
    max_y = max(p[:,1])
    max_z = max(p[:,2])
    diag = np.sqrt( (max_x - min_x)**2 + (max_y -min_y)**2 + (max_z -min_z)**2 )
    return diag
    

    

def extract_swc(file):
    '''Extracts the position data, radius data, connectivity data and the type data from a swc file'''

    position_data = []
    radius_data = []
    conn_data = []
    type_data = []
    preamble = []

            # parse swc file
    with open(file, 'r') as f:
        first_node = True
        found_scale = False
        for iline in f:
            line = iline.strip().lower().split()

            # get the scale
            if 'scale' in line:
                if line[0] == '#':
                    scale = np.array(line[2:5], dtype=float)
                else:
                    scale = np.array(line[1:4], dtype=float)
                found_scale = True
            # read nodes
            elif len(line) == 7 and line[0].isnumeric():
                # check the parent compartment of the first node
                if not(found_scale):
                    scale = np.array([1,1,1])
                    found_scale = True

                if first_node and int(line[6]) != -1:
                    raise ValueError(
                        "Parent of the first node must be -1.")
                else:
                    first_node = False

                # extract info
                id = int(line[0]) - 1
                node_type = int(line[1])
                position = scale * np.array(line[2:5], dtype=float)
                radius = float(line[5])
                parent_id = int(line[6]) - 1

                # check parameters
                if parent_id < 0:
                    parent_id = -1

                if parent_id == -1 and node_type != 1:
                    node_type = 1
                    msg = "Soma absent. Convert the first point to soma."
                    warnings.warn(msg, RuntimeWarning, stacklevel=2)

                # if parent_id >= id:
                    # msg = " ".join((
                    #     f"Node id {line[0]}:",
                    #     "parent id must be less than children id."))
                    # raise ValueError(msg)

                if id < 0:
                    msg = f"Node id {line[0]}: negative compartment ID."
                    raise ValueError(msg)

                if radius <= 0:
                    msg = f"Node id {line[0]}: negative radius."
                    raise ValueError(msg)
                # if radius < 0.1:
                #     radius = 0.1

                if node_type < 0 or node_type > 7:
                    msg = " ".join((
                        f"Node id {line[0]}:",
                        "unknown compartment type."))
                    raise TypeError(msg)

                # record info
                position_data.append(position)
                type_data.append(node_type)
                radius_data.append(radius)
                conn_data.append(np.array([id, parent_id]))
            else:
                preamble.append(iline)

    position_data= np.array(position_data)
    type_data= np.array(type_data)
    radius_data= np.array(radius_data)
    conn_data= np.array(conn_data)
    return position_data , radius_data, conn_data , type_data, preamble

def add_node_between_parent(i,num_points,position_data,radius_data,conn_data,type_data):
    "Adds linearly interpolated node between a node and it's parent"
    N = len(position_data) + num_points
    parent_id = conn_data[i][1]
    p = position_data[i]
    q = position_data[parent_id]
    r = radius_data[i]
    R = radius_data[parent_id]
    new_position_data = np.zeros((N,3))
    new_radius_data = np.zeros(N)
    new_type_data = np.zeros(N)
    new_conn_data = np.zeros((N,2))
    
    new_position_data[0:i] = position_data[0:i]
    new_radius_data[0:i] = radius_data[0:i]
    new_type_data[0:i] = type_data[0:i]
    new_conn_data[0:(i+1)] = conn_data[0:(i+1)]


    for j in range(0,num_points):
        l = (j+1)/(num_points + 1)
        new_position_data [(j+i)] = (1-l)*q + l*p
        new_radius_data[j+i] =  R**((1-l))*r**l
        new_conn_data[j+1+i] = np.array([j+1+i,i+j])
    new_type_data[i:(i+num_points)] += type_data[i] 
    new_position_data[i+num_points:] = position_data[i:]
    new_radius_data[i+num_points:] = radius_data[i:]
    new_type_data[i+num_points:] = type_data[i:]

    new_conn_data[(1+i+num_points):,1] = conn_data[1+i:,1]
    new_conn_data[(1+i+num_points):,0] = conn_data[1+i:,0] + num_points
    
    for j in range(i+num_points+1,N):
        if new_conn_data[j,1] >= i:
            new_conn_data[j,1] = new_conn_data[j,1] + num_points

    return new_position_data,new_radius_data,np.array(new_conn_data,dtype = int),np.array(new_type_data,dtype = int)

def node_merge_with_parent(i,position_data,radius_data,conn_data,type_data):
    "Merges a node with it's parent"
    N = len(position_data) - 1
    parent_id = conn_data[i][1]
    p = position_data[i]
    q = position_data[parent_id]
    r = radius_data[i]
    R = radius_data[parent_id]

    mean_position = (p+q)/2
    mean_radius = np.sqrt(r*R)

    new_position_data = np.zeros((N,3))
    new_radius_data = np.zeros(N)
    new_type_data = np.zeros(N)
    new_conn_data = np.zeros((N,2))
    
    new_position_data[0:i] = position_data[0:i]
    new_radius_data[0:i] = radius_data[0:i]
    new_type_data[0:i] = type_data[0:i]
    new_conn_data[0:i] = conn_data[0:i]
    
    new_position_data[parent_id] = mean_position
    new_radius_data[parent_id] = mean_radius

    new_position_data[i:] = position_data[(1+i):]
    new_radius_data[i:] = radius_data[(1+i):]
    new_type_data[i:] = type_data[(1+i):]
    new_conn_data[i:] = conn_data[(1+i):]

    new_conn_data[i:,0] = new_conn_data[i:,0]  - 1

    for j in range(i,N):
        if new_conn_data[j,1] > i:
            new_conn_data[j,1] = new_conn_data[j,1] - 1
        elif new_conn_data[j,1] == i:
            new_conn_data[j,1] = parent_id
    return  new_position_data,new_radius_data,np.array(new_conn_data,dtype = int),np.array(new_type_data,dtype = int)

def smooth_swc(position_data,radius_data,conn_data,type_data,Delta):
    N = len(position_data)
    num_children = [int(sum(conn_data[:,1] == i)) for i in range(0,N)]
    i = 0
    while i < N:
        p = position_data[i]
        if conn_data[i][1] >= 0  and type_data[i] != 1 and type_data[conn_data[i][1]] != 1:
            parent_id = conn_data[i][1]
            q = position_data[parent_id]
            r = radius_data[i]
            R = radius_data[parent_id]
            radius_ratio_flag = r/R >2 or R/r >2
            num_siblings = num_children[parent_id] - 1
            if norm(p-q) < Delta and num_children[i] == 1 and num_siblings == 0 and not(radius_ratio_flag):
                'Merge nodes'
                position_data,radius_data,conn_data,type_data = node_merge_with_parent(i,position_data,radius_data,conn_data,type_data)
                N = N -1
                num_children.pop(i)
            elif radius_ratio_flag:
                'Add interpolated nodes'
                num_points = int(np.min([3,np.floor(np.max([r/R,R/r]))]))
                position_data,radius_data,conn_data,type_data= add_node_between_parent(i,num_points,position_data,radius_data,conn_data,type_data)
                i = i + num_points + 1
                N = N + num_points
                for j in range(0,num_points):
                    num_children.insert(i+j,1)
                
            elif norm(p-q) > 2*Delta:
                'Add interpolated nodes'
                num_points = int(np.min([3,np.floor(norm(p-q)/Delta - 1)]))
                position_data,radius_data,conn_data,type_data= add_node_between_parent(i,num_points,position_data,radius_data,conn_data,type_data)
                i = i + num_points + 1
                N = N + num_points
                for j in range(0,num_points):
                    num_children.insert(i+j,1)
            else:
                i +=1
        else:
            i += 1
    return position_data,radius_data,conn_data,type_data


def  interpolate_swc( position_data , radius_data, conn_data , type_data,delta):
    soma_ind = np.where(type_data==1)[0]
    soma_position = position_data[soma_ind]
    max_soma_radii = np.max(radius_data[soma_ind])
    i = -1
    N = len(position_data)
    while i < N - 1:
        i = i + 1
        if conn_data[i][1] != -1 and type_data[i] != 1:
            p = position_data[i]
            parent_id = conn_data[i][1]
            q = position_data[parent_id]
            if norm(p-q) >= 2*delta:
                'Add interpolated nodes'
                num_points = int(np.floor(norm(p-q)/delta - 1))
                position_data,radius_data,conn_data,type_data= add_node_between_parent(i,num_points,position_data,radius_data,conn_data,type_data)
                i = i + num_points
                N = N + num_points
        
    return position_data , radius_data, conn_data , type_data


def create_branches(conn_data,type_data):
    N = len(conn_data)
    branches = np.zeros(N,dtype=int)
    id = 1
    children = [np.where(conn_data[:,1] == i)[0] for i in range(0,N)]
    num_children = [len(c) for c in children]
    junction_ind = [i for (i,n) in enumerate(num_children) if n > 1 or type_data[i] == 1]
    i = 0
    while i <N:
        if i in junction_ind:
            branches[i] = -1
        elif branches[i]==0:
            j = i
            while branches[j] == 0 and num_children[j]<=1:
                branches[j] = id
                if num_children[j] ==1:
                    j = children[j][0]
                else:
                    break
            id  += 1
        i +=1
            
    return branches

def reorder_swc(position_data,radius_data,conn_data,type_data):
    '''Reorders nodes to ensure parents always come before children'''
    N = len(conn_data)
    permutation = np.zeros(N)
    nodes = conn_data[:,0]
    parents = conn_data[:,1]
    source = nodes[parents == -1]
    if len(source) > 1:
        error('Swc file can only have one source node');
    permutation[source] = 0
    permutation[0] = source
    set= 0
    start_node = 0

    permutation,set = reorder(start_node,set,nodes,parents,permutation)
    permutation = np.array(permutation).astype(int)
    conn_data = conn_data[permutation]
    for i in range(0,N):
        mask = conn_data == conn_data[i,0]
        mask2 = conn_data == i
        conn_data[mask2] = conn_data[i,0]
        conn_data[mask] = i

    position_data = position_data[permutation]
    type_data = type_data[permutation]
    radius_data = radius_data[permutation]

    return position_data,radius_data,conn_data,type_data

def  reorder(start_node,set,nodes,parents,permutation):
    children = np.where(parents == start_node)[0]
    for i in range(0,len(children)):
        set = set + 1
        permutation[set] = children[i]
        permutation,set = reorder(children[i],set,nodes,parents,permutation)
    return permutation,set