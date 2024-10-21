# $output_dir ="C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid_surface_new\separated";
$output_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid_surface_true";

mkdir $output_dir;
Get-ChildItem -Path C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid\*.swc -Recurse -Force -Filter *.swc | Foreach-Object{

$cellname = $_.BaseName; $path = Split-Path -Path $_;
echo $cellname;
cp $path/$cellname.wrl $output_dir/$cellname.wrl;
cp $path/$cellname.swc $output_dir/$cellname.swc;
$output = $output_dir+"/"+$cellname+".ply";
# echo $output
# python fix_swc.py $path/$cellname.swc $output_dir;
# python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=2000 --segment_meshes=1;
# python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=2000;
if (!(Test-Path $output)){
# python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=6000 --alpha=0.001 --log=1;
python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --simplify=0 --alpha=0.001 --log=1;

}
Remove-Item $output_dir/$cellname.wrl;
Remove-Item $output_dir/$cellname.swc;

}
