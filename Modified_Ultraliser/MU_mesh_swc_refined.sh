#!/bin/bash

path_to_Ultraliser=Modified_Ultraliser/Ultraliser/build/bin;

function mesh {
file="$1";
voxels_per_micron=$2;
# Create temporary directories for 
echo "Organizing temporary directories"
fbname=$(basename "$file" .swc)
name=${fbname%".CNG"}
temp=$output/$fbname;
rm -rf $temp;
mkdir $temp;
logfile=$output/$fbname"_log.txt";
echo $fbname >> $logfile;

echo "Applying soma";
time_soma="$(time (python MU_mesh_soma.py $file --output_dir=$temp) 2>&1 1>/dev/null )"

echo $file
echo "Applying skeleton"
time_skeleton="$(time ($path_to_Ultraliser/ultraNeuroMorpho2Mesh --morphology=$file --output-directory=$temp --export-ply-mesh  --ignore-marching-cubes-mesh --ignore-laplacian-mesh  --scaled-resolution --voxels-per-micron=$voxels_per_micron)  2>&1 1>/dev/null )"
meshfile=$temp/meshes/$name-watertight.ply
if ! [ -f $meshfile ]; then
    echo "No skelton produced by Ultraliser" >> $logfile;
    return [n];
fi;

mv $temp/meshes/$name-watertight.ply $temp/$fbname-watertight.ply
rmdir $temp/meshes


echo "Applying merge with Ultraliser";
time_merging="$(time ($path_to_Ultraliser/ultraMeshes2Mesh --input-directory=$temp --output-directory=$temp --export-ply-mesh --ignore-marching-cubes-mesh --ignore-laplacian-mesh  --scaled-resolution --voxels-per-micron=$voxels_per_micron)  2>&1 1>/dev/null )"
mv $temp/meshes/$fbname-watertight.ply $temp/$fbname.ply;
rmdir $temp/meshes;
cp $temp/$fbname.ply $temp/$fbname"-non-simplified.ply";

echo "Applying simplification";
time_simplifying="$(time (python simplify_mesh.py $file $temp/$fbname.ply --output_dir=$output)  2>&1 1>/dev/null )"
echo "Uncomment line below to only save final mesh";
# rm -rf $temp

echo "Writing times";
echo "Soma meshing" >> $logfile;
echo "$time_soma" >> $logfile;
echo "Skeleton meshing" >> $logfile;
echo "$time_skeleton" >> $logfile;
echo "Merging meshes" >> $logfile;
echo "$time_merging" >> $logfile;
echo "Simplifying mesh" >> $logfile;
echo "$time_simplifying" >> $logfile;

# rm -rf $temp
echo "Meshed $fbname"
}

voxels_per_micron=8

output=Modified_Ultraliser/output_refined_$voxels_per_micron
mkdir $output


echo "Producing mesh for 1-2-1.CNG.swc"
file=input/1-2-1.CNG.swc;
mesh $file $voxels_per_micron

echo "Producing mesh for 1-2-2.CNG.swc"
file=input/1-2-2.CNG.swc; 
mesh $file $voxels_per_micron

echo "Producing mesh for 04b_spindle3aFI.swc"
file=input/04b_spindle3aFI.swc; 
mesh $file $voxels_per_micron