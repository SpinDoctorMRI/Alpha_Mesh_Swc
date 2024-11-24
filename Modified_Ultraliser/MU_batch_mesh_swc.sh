#!/bin/bash

path_to_Ultraliser=Modified_Ultraliser/Ultraliser/build/bin;

function mesh {
file="$1";

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
time_skeleton="$(time ($path_to_Ultraliser/ultraNeuroMorpho2Mesh --morphology=$file --output-directory=$temp --export-ply-mesh  --ignore-marching-cubes-mesh --ignore-laplacian-mesh)  2>&1 1>/dev/null )"
meshfile=$temp/meshes/$name-watertight.ply
if ! [ -f $meshfile ]; then
    echo "No skelton produced by Ultraliser" >> $logfile;
    rm -rf $temp;
    return [n];
fi;

mv $temp/meshes/$name-watertight.ply $temp/$fbname-watertight.ply
rmdir $temp/meshes


echo "Applying merge with Ultraliser";
time_merging="$(time ($path_to_Ultraliser/ultraMeshes2Mesh --input-directory=$temp  --output-directory=$temp --export-ply-mesh --ignore-marching-cubes-mesh --ignore-laplacian-mesh)  2>&1 1>/dev/null )"
mv $temp/meshes/$fbname-watertight.ply $temp/$fbname.ply;
rm -rf $temp/meshes;
# cp $temp/$fbname.ply $temp/$fbname"-non-simplified.ply";

echo "Applying simplification";
time_simplifying="$(time (python simplify_mesh.py $file $temp/$fbname.ply --output_dir=$output)  2>&1 1>/dev/null )"
# echo "Uncomment line below to only save final mesh";
rm -rf $temp

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

mkdir Modified_Ultraliser/output

echo "Set input swc files here:";
input=1000_swc_files;
output=Modified_Ultraliser/output;

echo "Meshing $input";
for file in $input/*.swc; do
    fbname=$(basename "$file" .swc);
    meshfile="$output/$fbname.ply";
    logfile=$output/$fbname"_log.txt";
    if [ -f $logfile ]; then
    echo "$logfile already exists\nSkipping mesh";
    else
    echo "Meshing $file";
    mesh $file;
    fi
done;

