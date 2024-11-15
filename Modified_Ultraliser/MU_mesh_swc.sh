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
echo $fbname >> $logfile;

echo "Applying soma";
time_soma="$(time (python MU_mesh_soma.py $file --output_dir=$temp) 2>&1 1>/dev/null )"

echo $file
echo "Applying skeleton"
time_skeleton="$(time ($path_to_Ultraliser/ultraNeuroMorpho2Mesh --morphology=$file --output-directory=$temp --export-ply-mesh  --ignore-marching-cubes-mesh --ignore-laplacian-mesh)  2>&1 1>/dev/null )"
meshfile=$temp/meshes/$name-watertight.ply
if ! [ -f $meshfile ]; then
    echo "No skelton produced by Ultraliser";
    return [n];
fi;

mv $temp/meshes/$name-watertight.ply $temp/$fbname-watertight.ply
rmdir $temp/meshes


echo "Applying merge with Ultraliser";
time_merging="$(time ($path_to_Ultraliser/ultraMeshes2Mesh --input-directory=$temp  --output-directory=$temp --export-ply-mesh --ignore-marching-cubes-mesh --ignore-laplacian-mesh)  2>&1 1>/dev/null )"
mv $temp/meshes/$fbname-watertight.ply $temp/$fbname.ply;
rmdir $temp/meshes;
cp $temp/$fbname.ply $temp/$fbname"-non-simplified.ply";

echo "Applying simplification";
time_simplifying="$(time (python simplify_mesh.py $file $temp/$fbname.ply --output_dir=$output)  2>&1 1>/dev/null )"

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
file=input/1-2-1.CNG.swc; output=Modified_Ultraliser/output; logfile=Modified_Ultraliser/output/1-2-1.CNG/log.txt
mesh $file


# mkdir $output
# for file in $input/*.swc; do
# fbname=$(basename "$file" .swc);
# meshfile="$output/$fbname.ply";
# echo $meshfile;
# if [ -f $meshfile ]; then
# echo "$meshfile already exists";
# else
# echo $file;
# mesh $file;
# fi
# done;

