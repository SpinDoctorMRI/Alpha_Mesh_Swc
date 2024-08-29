import numpy as np
import scipy
from numpy.linalg import norm

def make_faces(n,N):
    """" Create cylindrical faces along tubular mesh.
    
    Args:
        n: (int) number of vertices along each disk along the mesh
        N: (int) number of vertices in mesh so far
    
    """
    old_indices = N-n+ np.arange(0,n,1)
    new_indices = N + np.arange(0,n,1)
    f = np.zeros((2*n,3))
    f[0:n,0] = old_indices
    f[0:n,1] = new_indices
    f[0:n,2] = np.roll(new_indices,1)
    f[n:,0] = new_indices
    f[n:,1] = old_indices
    f[n:,2] = np.roll(old_indices,-1)
    return f

def make_initial_vertices(tendril,n):
    """Make an initial disk for the tubular mesh
    
    Args:
        tendril: (Tendril)
        n: (int) number of vertices along disk

    """
    # Get initial point,radius, and direction
    p = tendril.p[0].reshape((3,1))
    r = tendril.r[0]
    t = tendril.skeleton(x=0,nu=1)
    t= t/norm(t)

    # Create uniform disk in z =0 plane
    theta = 2*np.pi*np.arange(0,n,1)/n
    points = np.vstack((r*np.cos(theta),r*np.sin(theta),np.zeros(n)))

    # Transform to  initial point,radius and direction
    R = make_rotation_matix(np.array([0,0,1]),t)
    points = np.dot(R,points) + p
    return points

def make_rotation_matix(dir1,dir2):
    """"Create a rotation matrix R which sends dir_1, to dir_2 
    Args:
        dir_1: (3,) numpy.array 
        dir_2: (3,) numpy.array 
    """

    # Normalise directions
    dir1 = dir1/norm(dir1)
    dir2 = dir2/norm(dir2)

    u = np.cross(dir1,dir2)
    s = norm(u)
    
    if abs(s)>=0.0000001:
         u = u/s
    c = np.dot(dir1,dir2)
    theta = np.arctan2(s,c)
    kx = u[0]; ky=u[1]; kz=u[2]
    K = np.array([[0,-kz,ky],[ kz,0,-kx],[-ky,kx,0]])
    Kout = np.outer(u,u)    
    R = np.eye(3)*c+s*K + (1-c)*Kout
    return R

class Tendril():
    """Class representing a single branch of a neuron swc file. Computes a tubular mesh 
    
    attributes:
        nodes: (numpy.array) indices of nodes in branch
        swc: (Swc) neuron swc data
        Delta: (float) relevent distance for computing spline
    
    methods:
        make_splines: create splines to interpolate nodes position and radii
        make_mesh: create tubular mesh
        transport: move points along the branch
    """


    def __init__(self,nodes,swc,Delta):
        self.nodes = nodes
        self.p = swc.position_data[nodes]
        self.r = swc.radius_data[nodes]
        self.Delta = Delta
        self.make_splines()
        return None
    def make_splines(self):
        """Make splines to interpolate position and radii of nodes"""
        n = len(self.p)
        t = np.zeros(n)
        for i in range(1,n):
            t[i] = t[i -1 ]+norm(self.p[i] - self.p[i-1])
        L = t[-1]
        # s = [0]
        # print(f'Delta = {self.Delta}')
        # for i in range(1,n):
        #     if t[i] - s[-1] >= self.Delta or i == n-1:
        #         s.append(i)
        #     else:
        #         print('Rejecting node')
        # s = np.array(s)
        # p = self.p[s]
        # t = t[s]/L
        t = t/L
        p = self.p
        self.skeleton = scipy.interpolate.CubicSpline(t, p,bc_type = 'natural',extrapolate=None)
        # self.radius = scipy.interpolate.CubicSpline(t, self.r[s],bc_type = 'natural',extrapolate=None)
        self.radius = scipy.interpolate.CubicSpline(t, self.r,bc_type = 'natural',extrapolate=None)

        self.L = L
        return self
    def make_mesh(self,v_S,f_S):
        """Makes tubular mesh
        Args:
            v_S: (N,3) array of vertices from a unit sphere mesh.
            f_S: (M,3) array of faces from a unit sphere mesh.
        """

        # Create initial disk and judge length of step size
        n = int(max([5,np.floor(15*np.mean(self.r))]))
        # n=5
        v0 = make_initial_vertices(self,n)
        steps = int(max([np.floor(self.L/(2*np.pi*np.mean(self.r)/(np.sqrt(2)*n))),3]))
        
        # Transport vertices along and create faces.
        v = [v0]
        f = []
        t = np.linspace(0,1,steps)
        for i in range(1,steps):
            v1 = self.transport(t[i-1],t[i],v0)
            v0 = v1.astype(float)
            f1 = make_faces(n,i*n)
            f.append(f1)
            v.append(v1)

        v = np.hstack(v).T
        
        # Add spherical caps
        start = self.skeleton(x = 0)
        end = self.skeleton(x=1)
        N = len(v)
        v=np.vstack((v,self.r[0]*v_S + start,self.r[-1]*v_S + end))
        f.append(f_S+N)
        f.append(f_S+N+len(v_S))        
        f = np.vstack(f).astype(int)
        return v,f
    
    def transport(self,t1,t2,v):
        """
        Moves vertices perpindicular to the position spline at t1 to correpsonding displacements from spline at t2
        """

        # Obtain positions and directions
        p1 = self.skeleton(x=t1,nu=0).reshape((3,1))
        p2 = self.skeleton(x=t2,nu=0).reshape((3,1))
        d1 = self.skeleton(x=t1,nu=1)
        d2 = self.skeleton(x=t2,nu=1)

        r_min = min(self.r)
        r_max = max(self.r)
        r1 = min([max([r_min,self.radius(x=t1)]),r_max ])
        # Rescale vertices to unit distance from origin
        v = (v-p1)/r1
        r2 = min([max([r_min,self.radius(x=t2)]),r_max ])

        # Compute change of direction matrix
        R = make_rotation_matix(d1,d2)

        # Remap points
        v = r2*np.matmul(R,v) + p2
        return v
        