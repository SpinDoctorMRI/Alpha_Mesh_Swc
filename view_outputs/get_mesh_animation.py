
# Need open3d (in my base environment)
from open3d import io, visualization 
import sys 


def custom_draw_geometry_with_rotation(pcd,animation_path):

    custom_draw_geometry_with_rotation.index= 0

    def rotate_view(vis):
        ctr = vis.get_view_control()
        custom_draw_geometry_with_rotation.index +=1
        ctr.rotate(10.0, 0.0)
        vis.capture_screen_image(f'{animation_path}/frame_{custom_draw_geometry_with_rotation.index}.png',do_render=True)
        if custom_draw_geometry_with_rotation.index > 2094.3951/10 :
            vis.\
                register_animation_callback(None)
        return False

    visualization.draw_geometries_with_animation_callback([pcd],rotate_view)
    
def main(file,animation_path):
    mesh = io.read_triangle_mesh(file) # Read point cloud
    custom_draw_geometry_with_rotation(mesh,animation_path)

if __name__=='__main__':
    main(sys.argv[1],sys.argv[2])
