# $output_dir ="C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified_surface_new\separated";
$output_dir ="C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified_surface_true";

mkdir $output_dir

Get-ChildItem -Path C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified\*.swc -Recurse -Force -Filter *.swc |
Foreach-Object{

$cellname = $_.BaseName; $path = Split-Path -Path $_;
echo $cellname;
cp $path/$cellname.wrl $output_dir/$cellname.wrl;
cp $path/$cellname.swc $output_dir/$cellname.swc;
$output = $output_dir+"/"+$cellname+".ply";

# python fix_swc.py $path/$cellname.swc $output_dir;
# python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=2000 --segment_meshes=1;
if (!(Test-Path $output)){
    # python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=6000 --alpha=0.005 --log=1;
    python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --simplify=0 --alpha=0.001 --log=1;
    }
Remove-Item $output_dir/$cellname.wrl;
Remove-Item $output_dir/$cellname.swc;

}

# $source = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified\ctrl_210219_10_781-5_1.swc";
# Remove-Item "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified_surfaces_new\ctrl_210219_10_781-5_1.ply";
# $cellname = (Get-Item $source).BaseName; $path = Split-Path -Path $source;
# echo $cellname;
# cp $path/$cellname.wrl $output_dir/$cellname.wrl;
# # cp $path/$cellname.swc $output_dir/$cellname.swc;
# python fix_swc.py $path/$cellname.swc $output_dir;
# python mesh_microglia.py $output_dir\$cellname --output_dir=$output_dir --min_faces=2000;

# Remove-Item $output_dir/$cellname.wrl;
# Remove-Item $output_dir/$cellname.swc;