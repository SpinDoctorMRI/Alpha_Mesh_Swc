# Need open3d (in my base environment)
from open3d import io, visualization 
import sys 

def main(file):
    cloud = io.read_point_cloud(file+'_pc.ply') # Read point cloud
    mesh = io.read_triangle_mesh(file + '.ply') # Read point cloud

    visualization.draw_geometries([cloud,mesh])    

if __name__=='__main__':
    main(sys.argv[1])