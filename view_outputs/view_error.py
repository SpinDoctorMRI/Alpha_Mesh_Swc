# Need open3d (in my base environment)
from open3d import io, visualization 
import argparse 

def main(mesh_file,point_cloud_file):
    cloud = io.read_point_cloud(point_cloud_file) # Read point cloud
    mesh = io.read_triangle_mesh(mesh_file) # Read point cloud

    visualization.draw_geometries([cloud,mesh])    

if __name__=='__main__':
    description = '''Visualise the Skeleton to Mesh Error alongside the surface mesh'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("mesh", help="Input mesh.")
    parser.add_argument("point_cloud", help="Input point cloud")

    args = parser.parse_args()
    mesh_file = args.mesh
    point_cloud_file = args.point_cloud
    main(mesh_file,point_cloud_file)