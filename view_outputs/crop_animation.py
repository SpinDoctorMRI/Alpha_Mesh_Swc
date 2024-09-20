from PIL import Image
import numpy as np
import os
import sys
from get_point_cloud_image import make_transparent
from alive_progress import alive_bar
import time
def find_box(im):
    pix = np.asarray(im)

    pix = pix[:,:,0:3] # Drop the alpha channel
    idx = np.where(pix-255)[0:2] # Drop the color when finding edges
    box = list(map(min,idx))[::-1]+ list(map(max,idx))[::-1]
    return box

def crop_image(im,box):
    region = im.crop(box)
    region_pix = np.asarray(region)
    im  = Image.fromarray(region_pix)
    return im


if __name__=='__main__':
    dir = sys.argv[1]
    files = os.listdir(dir)
    boxes = []
    nfiles = len(files)
    print('Finding boxes')
    with alive_bar(nfiles) as bar:
        for file in files:
            im = Image.open(os.path.join(dir,file))
            box = find_box(im)
            boxes.append(box)
            bar()

    boxes = np.asarray(boxes)
    box = [np.min(boxes[:,0]),np.min(boxes[:,1]),np.max(boxes[:,2]),np.max(boxes[:,3]) ]
    print('Cropping images')
    with alive_bar(nfiles) as bar:
        for file in files:
            im = Image.open(os.path.join(dir,file))
            im = crop_image(im,box)
            im = make_transparent(im)
            im.save(os.path.join(dir,file))
            bar()
