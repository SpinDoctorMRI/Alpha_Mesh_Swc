# $mesh_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid_surface_new";
# $source_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid";
# $output_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Amoeboid_accuracy_new";

$mesh_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified_surface_new";
$source_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified";
$output_dir = "C:\Users\amcsween\Documents\GitHub\MicrogliaSet\MicrogliaConverted_Alex\Ramified_accuracy_new";

# $mesh_dir = "C:\Users\amcsween\Desktop\Ultraliser_modified_comparison\Human_microglia\Amoeboid_meshes";
# $source_dir = "C:\Users\amcsween\Desktop\Ultraliser_modified_comparison\Human_microglia\Amoeboid_source";
# $output_dir = "C:\Users\amcsween\Desktop\Ultraliser_modified_comparison\Human_microglia\Amoeboid_accuracy";


mkdir $output_dir;

cd ..

Get-ChildItem -Path $mesh_dir\*.ply -Recurse -Force -Filter *.ply |
Foreach-Object{
$cellname = $_.BaseName;
python microglia_accuracy.py $mesh_dir\$cellname.ply $source_dir\$cellname.swc $output_dir\$cellname.txt 1 ;
}
