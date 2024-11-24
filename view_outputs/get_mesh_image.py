import sys
import open3d as o3d
from PIL import Image
from get_point_cloud_image import crop_image,make_transparent



if __name__ =='__main__':
    mesh_name=sys.argv[1]
    
    mesh = o3d.io.read_triangle_mesh(mesh_name)
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False) #works for me with False, on some systems needs to be true
    vis.add_geometry(mesh,mesh_show_wireframe=True)
    vis.update_geometry(mesh)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(mesh_name.replace('.ply','.png'),do_render=True)
    vis.destroy_window()
 
 
    im = Image.open(mesh_name.replace('.ply','.png'))
    im = crop_image(im)
    im = make_transparent(im)
    im.save(mesh_name.replace('.ply','.png'))