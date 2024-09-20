# Need open3d (in my base environment)
from open3d import io, visualization 
import sys 


def main(file):
    cloud = io.read_triangle_mesh(file) # Read point cloud
    visualization.draw_geometries([cloud],mesh_show_wireframe=True)    

if __name__=='__main__':
    main(sys.argv[1])