# alphaSwc
Alpha wrapping of neurons from swc files for watertight surface meshes

To run on an individual swc file and save the mesh to VALID_DIRECTORY, run
python mesh_swc.py PATH_TO_FILE --ouput_dir=VALID_DIRECTORY

To loop over all swc files in a directory and save meshes with statistics to OUTPUT_DIRECTORY, run 
python mesh_many_swc.py INPUT_DIRECTORY OUTPUT_DIRECTORY
