# Alpha_Mesh_Swc

This is a software package designed to automatically generate accurate watertight surface meshes from swc files for simulation purposes. The paper introducing and describing the package will be linked here upon publication.

----

## Paper scripts

To install the repositery and access these scripts run:
```
    git clone https://github.com/SpinDoctorMRI/Alpha_Mesh_Swc;
    cd Alpha_Mesh_Swc;
    git checkout Paper_Scripts;
```

To install the necessary python prerequisites run:
```
pip install -r requirements.txt
```

### Neurons
To run the two neurons tested in section 4.1 run:

```
mkdir output;
python mesh_swc.py input/04b_spindle3aFI.swc --output_dir=output;
python mesh_swc.py input/1-2-1.CNG.swc --output_dir=output;
```

To obtain the Skeleton to Mesh Error run:

```
python SkeletonMeshError.py output/04b_spindle3aFI.ply input/04b_spindle3aFI.swc output/04b_spindle3aFI_SME.txt --save_pc==1;
python SkeletonMeshError.py output/1-2-1.CNG.ply input/1-2-1.CNG.swc output/1-2-1.CNG_SME.txt --save_pc==1;
```

The Skeleton to Mesh Error is the RMS value in the *_SME.txt file. To visualize the full distribution of the scalar field d, run

```
python view_outputs/view_point_cloud.py output/04b_spindle3aFI_pc.ply;
python view_outputs/view_point_cloud.py output/1-2-1.CNG_pc.ply;
```

Visualizing the surface meshes can be done in 3rd party software (e.g. Windows 3d viewer) or by running:

```
python view_outputs/add_color.py output/04b_spindle3aFI.ply;
python view_outputs/view_ply.py output/04b_spindle3aFI.ply;

python view_outputs/add_color.py output/1-2-1.CNG.ply;
python view_outputs/view_ply.py output/1-2-1.CNG.ply;
```

The surface meshes and point clouds can be plotted in the same window with:

```
python view_outputs/view_error.py output/04b_spindle3aFI.ply output/04b_spindle3aFI_pc.ply;
python view_outputs/view_error.py output/1-2-1.CNG.ply output/1-2-1.CNG.ply;
```

### Microglia
To create the microglia meshes run:

```bash
mkdir Microglia/Amoeboid_output
for file in Microglia/Amoeboid/*.swc; do
    cellname="${file%.*}";
    echo "Meshing $cell";
    python mesh_microglia.py $cellname --log=1 --output_dir=Microglia/Amoeboid_output --alpha=0.001;
done

mkdir Microglia/Ramified_output
for file in Microglia/Ramified/*.swc; do
    cellname="${file%.*}";
    echo "Meshing $cell";
    python mesh_microglia.py $cellname --log=1 --output_dir=Microglia/Ramified_output --alpha=0.001;
done
```

To test the accuracy of the microglia we run:

```bash
for file in Microglia/Amoeboid_output/*.ply; do
    meshname=$(basename $file);
    cellname="${meshname%.*}";
    python SkeletonMeshError.py $file "Microglia/Amoeboid/"$cellname".swc" "Microglia/Amoeboid_output"/$cellname"_SME.txt" --soma_mesh="Microglia/Amoeboid/"$cellname".wrl" --save_pc=1;
done

for file in Microglia/Ramified_output/*.ply; do
    meshname=$(basename $file);
    cellname="${meshname%.*}";
    python SkeletonMeshError.py $file "Microglia/Ramified/"$cellname".swc" "Microglia/Ramified_output"/$cellname"_SME.txt" --soma_mesh="Microglia/Ramified/"$cellname".wrl" --save_pc=1;
done
```

### 1-2-2.CNG
This cell was used to test the effect of Skeleton to Mesh Error on dMRI simulations. To compute the mesh and Skelton to Mesh Error run:
```
python mesh_swc.py input/1-2-2.CNG.swc --output_dir=output;
python SkeletonMeshError.py output/1-2-2.CNG.ply input/1-2-2.CNG.swc output/1-2-2.CNG_SME.txt --save_pc==1;
```
Visualise the results with:
```
python view_outputs/view_point_cloud.py output/1-2-2.CNG_pc.ply;
python view_outputs/add_color.py output/1-2-2.CNG.ply;
python view_outputs/view_ply.py output/1-2-2.CNG.ply;
```

### Diffusion MRI simulations
To do: Add link.

### Modified Ultraliser scripts
To do: Add description.

-----
## Setup and requirements

This can be done by running 
```
    pip install -r requirements.txt
```
To produce the surface meshes the following python requirements are needed:‘numpy’, ‘scipy’,‘trimesh’, ‘pymeshlab(version>=2023.12.post1)’. To produce the volume meshes TetGen [1] must be installed, which we include here.

TetGen is also used in our mesh algorithm to check the watertightness of the output mesh. If Python is unable to launch TetGen  an error is raised and instead a PyMeshLab filter is used instead. This filter is less accurate and may not always produce the desired outcome.

For some optional visualisation scripts in view_outputs  we use open3d. This is not used for anything other than visualisation.

-----
## How to use it

### Basic example
An individual mesh may be meshed with 
```
    python mesh_swc.py file=path/to/swc_file 
 ```

Optional parameters include:
    --output_dir = Output directory for mesh
    --alpha = Alpha fraction for alpha wrapping
    --Delta = Smoothing parameter for skeleton of swc file.
    --simplify = Flag to simplify mesh
    --min_faces = Minimum faces for the mesh
    --dfaces = Rate to increase target number of faces in mesh
    --tetgen_args = Parameters to pass into TetGen to generate finite element mesh
    --save_alpha_mesh = Flag to save alpha wrapping mesh

By default the mesh is saved with the input file, the simplification process runs and the alpha wrapping mesh is not saved. The parameters alpha, Delta, min_faces, dfaces are chosed as outlined in [cite paper].

If the user wishes to alter the min_faces,dfaces parameters using information from the input file or alpha wrapping mesh, we recommend setting the --simplify flag to 0, and then simplifying the saved mesh with the simplify_meshes.py script.

----
### Batch processesing
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

----
### Measuring Skeleton to Mesh Error
An individual Skeleton to Mesh Error is computed through
```
    python SkeletonMeshError.py path/to/mesh_file path/to/swc_file path/to/output_file
```
And saved to the output file. If an additional parameter is added to the command line then the point cloud along with the distances is saved with the mesh_file. Alongside the point cloud a color bar is saved as an image, to see the correspondance between hue and local mesh error. The point cloud can be visualised using open3d and 
```
    python view_outputs/view_point_cloud.py path/to/point_cloud_file
```
Multiple meshes can be assessed with 
```
    python batch_SkeletonMeshError.py directory_of_meshes directory_of_swc_files directory_of_outputs
```
Point clouds are not saved with this command.

----
### Meshing mixed descriptions (work in progress)

To mesh cells which consist of a separate swc file for the skelton and a surface mesh for the nodes it is necessary to follow the following proceedure.
Make sure that cellname.swc and cellname.wrl are saved in the same directory. To mesh the cell launch

```
    python mesh_microglia.py name=path/to/cellname
```
where file does not include the .swc or soma extension. Optional parameters include:
    --output_dir = Output directory for mesh
    --alpha = Alpha fraction for alpha wrapping
    --Delta = Smoothing parameter for skeleton of swc file.
    --simplify = Flag to simplify mesh
    --min_faces = Minimum faces for the mesh
    --segment_meshes = Flag to produce separate dendrite, and soma meshes.
    --soma_ext = File extension for soma mesh. Defaults to .wrl

Currently computing the mesh accuracy for mixed cell descriptions is not supported.
----
## Visualisation
On windows the surface meshes may be viewed with 3D viewer, available freely on the Microsoft store. For visualisation of surface meshes with this program run
```
    python view_outputs/view_ply.py path/to/mesh
```
Alternatively if open3d is installed as a package on python, you can use:
```
    python view_outputs/add_color.py path/to/mesh
    python view_outputs/view_surface_mesh.py path/to/mesh
```
The swc file can be viewed directly by running:
```
    python view_outputs/view_swc.py path/to/swc_file
```
If the point cloud was saved when running mesh_SME it can be viewed by using:
```
    python view_outputs/view_point_cloud.py path/to/point_cloud
```
The point cloud can be plotted alongside the mesh using 
```
    python view_outputs/add_color.py path/to/mesh
    python view_outputs/view_error.py path/to/cellname
```
where cellname is the name of the mesh file without any extension.
----
## Misc
check_femesh.py and check_femeshes.py are used to test the quality of finite element meshes but do not store them for storage purposes. To create finite element meshes use the surface mesh as an input to TetGen or other meshing software.


[1] Hang, S., 2015. TetGen, a Delaunay-based quality tetrahedral mesh generator. ACM Trans. Math. Softw, 41(2), p.11.