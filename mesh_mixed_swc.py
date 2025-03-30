from src import Swc, simplify_mesh
import argparse
import time
import os
import pymeshlab as mlab

if __name__ == "__main__":
    description = """Reads swc file and separate soma file and produces a coarse watertight surface mesh
            
    Use the flag --help to see all available options.
    """

    # Read parameters and flags
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("name", help="Input name of cell.")
    parser.add_argument("--log", type=str, default=None)
    parser.add_argument("--output_dir", help="Output directory for mesh", default="")
    parser.add_argument(
        "--alpha", help=" Alpha fraction for alpha wrapping", type=float, default=0.0025
    )
    parser.add_argument("--simplify", type=int, help="Flag to simplify mesh", default=1)
    parser.add_argument(
        "--Delta",
        type=float,
        default=0.05,
        help="Smoothing parameter for skeleton of swc file.",
    )
    parser.add_argument("--min_faces", help="Minimum faces for the mesh")
    parser.add_argument(
        "--segment_meshes", type=int, help="Flag to mesh separate segments", default=0
    )
    parser.add_argument("--soma_ext", help="Extension of soma file", default=".wrl")

    # Parse args
    args = parser.parse_args()
    min_faces = args.min_faces
    alpha_fraction = args.alpha

    # Get file paths
    dendrite_file = ".".join([args.name.replace("\r", ""), "swc"])
    cellname = os.path.basename(dendrite_file)
    output = os.path.join(args.output_dir, cellname.replace(".swc", ".ply"))
    log = args.log
    temp_dir_name = output.replace(".ply", "")

    # Create mesh for processes
    print(f"Loading {dendrite_file}")
    start = time.time()
    # Load Swc
    swc = Swc(dendrite_file, process=True, Delta=args.Delta, delta=args.Delta / 2)

    # Store simplification parameters
    if args.simplify == 1:
        r_min = min(swc.radius_data)
        total_length = swc.get_length()
        dfaces = int(total_length * 8)
        if min_faces is None:
            min_faces = dfaces
        else:
            min_faces = int(min_faces)
    print(f"segment_meshes={args.segment_meshes}")

    # Check for meshing full surface, or for creating separate meshes
    if args.segment_meshes != 1:
        # Only mesh full surface

        # Create meshset
        ms = mlab.MeshSet()
        # Create processes mesh
        ms_dendrites = swc._build_initial_mesh()
        # Store in main mesh set
        ms.add_mesh(ms_dendrites.current_mesh())
        # Load Soma mesh
        ms.load_new_mesh("".join([args.name.replace("\r", ""), args.soma_ext]))
        # Merge meshes
        ms.generate_by_merging_visible_meshes()

        # Apply alpha wrapping with an offset
        ms.generate_alpha_wrap(
            alpha_fraction=alpha_fraction, offset_fraction=alpha_fraction / 30
        )

        # Apply simplification algorithm
        if args.simplify == 1:
            ms = simplify_mesh(
                ms, dfaces, r_min / 2, min_faces, temp_dir_name=temp_dir_name
            )

        # Save mesh output
        ms.save_current_mesh(output, binary=False)
        print(f"Saved to {output}")

        # Write log output
        if log is not None:
            with open(output.replace(".ply", ".txt"), "w") as f:
                f.write(f"{time.time()-start:.2f}")
    else:
        # Get separate dendrite and soma meshes
        start_meshing = time.time()
        # Create processes mesh
        ms_dendrites, _, _ = swc.make_mesh(
            simplify=False, alpha_fraction=alpha_fraction, save=False
        )
        # Split processes mesh
        ms_dendrites.generate_splitting_by_connected_components(delete_source_mesh=True)
        meshing_time = time.time() - start_meshing

        # Apply simplification proceedure and save each process
        for i in range(0, ms_dendrites.mesh_number() - 1):
            # Store mesh in working mesh set
            ms_d = mlab.MeshSet()
            m = ms_dendrites.current_mesh()
            ms_d.add_mesh(m)
            # Simplify mesh
            if args.simplify == 1:
                start_simplify = time.time()
                ms_d = simplify_mesh(
                    ms_d, dfaces / 3, r_min, min_faces / 3, temp_dir_name=temp_dir_name
                )
            # Save mesh
            ms_d.save_current_mesh(
                output.replace(".ply", f"_process_{i+1}.ply"), binary=False
            )
            print("Saved to " + output.replace(".ply", f"_process_{i+1}.ply"))

            # Clear working meshset
            ms_dendrites.delete_current_mesh()

            # Write log output
            if log is not None:
                with open(output.replace(".ply", f"_process_{i+1}.txt"), "w") as f:
                    f.write(f"Meshing time : {meshing_time}")
                    if args.simplify == 1:
                        f.write(f"Simplifying time : {time.time()-start_simplify:.2f}")

        # Load soma mesh
        ms_soma = mlab.MeshSet()
        ms_soma.load_new_mesh(
            "".join([args.name.replace("\r", ""), args.soma_ext])
        )  # or wrl
        # Apply alpha wrap
        start_meshing = time.time()
        ms_soma.generate_alpha_wrap(
            alpha_fraction=alpha_fraction, offset_fraction=alpha_fraction / 30
        )
        meshing_time = time.time() - start_meshing
        # Simplify mesh
        if args.simplify == 1:
            start_simplify = time.time()
            ms_soma = simplify_mesh(
                ms_soma, dfaces / 3, r_min, min_faces / 3, temp_dir_name=temp_dir_name
            )

        # Save mesh
        ms_soma.save_current_mesh(output.replace(".ply", "_soma.ply"), binary=False)

        # Write log output
        if log is not None:
            with open(output.replace(".ply", "_soma.txt"), "w") as f:
                f.write(f"Meshing time : {meshing_time}")
                if args.simplify == 1:
                    f.write(f"Simplifying time : {time.time()-start_simplify:.2f}")
        print(f"Saved to" + output.replace(".ply", "_soma.ply"))

    print(f"Total Elapsed time = {time.time()-start:.2f}")
