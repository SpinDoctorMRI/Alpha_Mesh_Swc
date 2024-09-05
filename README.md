### SWC_mesher

This is a software package designed to automatically generate accurate watertight surface meshes from swc files for simulation purposes. The paper introducing and describing the package will be linked here upon publication.

-----
## Setup and requirements

This can be done by running 
```
    python setup.py
```
To produce the surface meshes the following python requirements are needed:‘numpy’, ‘scipy’,‘trimesh’, ‘pymeshlab(version>=2023.12.post1)’. To producethe volume meshes TetGen must be installed, which we include here.

-----
## How to use the code.

An individual mesh may be meshed with 
```
    python mesh_swc.py file=path/to/file.swc 
 ```

Optional parameters include:
    --output_dir = Output directory for mesh
    --alpha = Alpha fraction for alpha wrapping
    --Delta = Smoothing parameter for skeleton of swc file.
    --simplify = Flag to simplify mesh
    --min_faces = Minimum faces for the mesh
    --dfaces = Rate to increase target number of faces in mesh
    --tetgen_args = Parameters to pass into TetGen
    --save_alpha_mesh = Flag to save alpha wrapping mesh

By default the mesh is saved with the input file, the simplification process runs and the alpha wrapping mesh is not saved. The parameters alpha, Delta, min_faces, dfaces are chosed as outlined in [cite paper].

If the user wishes to alter the min_faces,dfaces parameters using information from the input file or alpha wrapping mesh, we recommend setting the --simplify flag to 0, and then simplifying the saved mesh with the simplify_meshes.py script.

----

Multiple meshes may be created with 
```
    python batch_mesh_swc.py input_dir
```
Optional parameters include:
    --output_dir = Output directory for mesh.
    --alpha = Alpha fraction for alpha wrapping.
    --Delta = Smoothing parameter for skeleton of swc file.
    --simplify = Flag to simplify mesh.
    --min_faces = Minimum faces for the mesh.
    --dfaces = Rate to increase target number of faces in mesh.
    --tetgen_args = Parameters to pass into TetGen.
    --save_alpha_mesh = Flag to save alpha wrapping mesh.
    --store_data = Flag to save meshing statistics into a .txt file.

If a mesh of a cell already exists in the output directory it is skipped, so if the file is interrupted it may be continued without any repetition.

