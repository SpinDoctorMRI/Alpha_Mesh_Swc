import sys
import matplotlib as mpl
import matplotlib.pyplot as plt
import open3d as o3d
from PIL import Image
import numpy as np

def crop_image(im):
    pix = np.asarray(im)

    pix = pix[:,:,0:3] # Drop the alpha channel
    idx = np.where(pix-255)[0:2] # Drop the color when finding edges
    box = list(map(min,idx))[::-1]+ list(map(max,idx))[::-1]

    region = im.crop(box)
    region_pix = np.asarray(region)
    im  = Image.fromarray(region_pix)
    return im

def make_transparent(im):
    rgba = im.convert('RGBA')
    datas = rgba.getdata()
    newData = []

    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    rgba.putdata(newData)
    return rgba


if __name__ =='__main__':
    '''Create image of local mesh error. 
    The point cloud and color bar should already have been created and saved in the same location as the mesh.
    Needs as input the full path of the mesh file without the extension.'''

    cell_root=sys.argv[1]
    pc_name = cell_root +'_pc.ply'
    cbar_name = cell_root +'_cbar.png'
    
    cloud = o3d.io.read_point_cloud(pc_name)
    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False) #works for me with False, on some systems needs to be true
    vis.add_geometry(cloud)
    vis.update_geometry(cloud)
    vis.poll_events()
    vis.update_renderer()
    vis.capture_screen_image(pc_name.replace('.ply','.png'),do_render=True)
    vis.destroy_window()
 
 
    images = [Image.open(x) for x in [pc_name.replace('.ply','.png'),cbar_name]]
    images[0] = crop_image(images[0])
    images = [make_transparent(im) for im in images]
    widths, heights = zip(*(i.size for i in images))
    new_im = Image.new('RGBA', (sum(widths), max(heights)))

    
    if heights[0] >= heights[1]:
        new_im.paste(images[0],(0,0))
        new_im.paste(images[1],(widths[0] ,heights[0] - heights[1]))
    else:
        new_im.paste(images[0],(0,(heights[1]-heights[0])//2))
        new_im.paste(images[1],(widths[0] ,0))
    new_im.save(cell_root+'_pc.png')