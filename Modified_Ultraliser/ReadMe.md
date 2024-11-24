# Modified Ultraliser
This is a modification of the meshing tool presented in [1] and available at (https://github.com/BlueBrain/Ultraliser).

A full tutorial on using Ultraliser is available at (https://github.com/BlueBrain/Ultraliser/wiki).
Download and build Ultraliser into the Modified Ultraliser directory using the instructions from (https://github.com/BlueBrain/Ultraliser/wiki/Installation).  
```bash
    cd Modified_Ultraliser;
    git clone https://github.com/BlueBrain/Ultraliser;
    cd Ultraliser && mkdir build && cd build;
    cmake ..;
    sudo apt-get install libtiff-dev libeigen3-dev libhdf5-dev libbz2-dev libzip-dev libfmt-dev libglm-dev;
    make -j 6; 
```
Alternatively if Ultraliser is installed in a different location, modify the *path_to_Ultraliser* variable at the beginnning of each script.

To run Modified Ultraliser on the 3 neurons 04b_spindle3aFI, 1-2-1.CNG, and 1-2-2.CNG  run from Alpha_Mesh_Swc:
```
    bash Modified_Ultraliser/MU_mesh_swc.sh;
```
04b_spindle3aFI is not meshed by Ultraliser so no mesh is produced. 
The final meshes are saved in Modified_Ultraliser/output along with text files showing the time of each stage. Intermediate meshes are also saved in the corresponding subdirectories of Modified_Ultraliser/output. 

To run Modified Ultraliser with adaptive resolution and a set voxels-per-micron run
```
    bash Modified_Ultraliser/MU_mesh_swc_refined.sh
```
The number of voxels per micron can be set on line 59 of the script and by default is set to 8. 

### Batch computations
To run Modified_Ultraliser on a large number of meshes, run:
```
    Modified_Ultraliser/MU_batch_mesh_swc.sh;
```
The input folder of swc files should be modified in line 62 of the MU_batch_mesh_swc.sh. The only difference between the two functions is that the intermediate meshes are not saved.
Once the meshes have been computed, the Skelton to Mesh Error can be computed and stored with the meshing data by running: 
```
    python batch_SkeletonMeshError.py Modified_Ultraliser/output 1000_swc_files Modified_Ultraliser/SME;
    python  Modified_Ultraliser/MU_get_data.py  Modified_Ultraliser/output  Modified_Ultraliser/Modified_Ultraliser_1000_Neurons_summary.db --SME_dir= Modified_Ultraliser/SME;
```
To run TetGen and test the quality of finite element meshes run
```
    python check_femeshes.py Modified_Ultraliser/output Modified_Ultraliser/FE_data Modified_Ultraliser/Modified_Ultraliser_1000_Neurons_summary.db;
```
This data can be viewed from the Modified_Ultraliser_1000_Neurons_summary.db file or in the plot_summary_data.ipynb.

## Microglia

Microglia cells can be meshed by running:
```
    bash Modified_Ultraliser/MU_mesh_microglia.sh;
```
Changing the parameters for min_faces and dfaces for the microglia meshes can be done in line 44.