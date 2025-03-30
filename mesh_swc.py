from src import Swc
import argparse
import time
from src.pytetgen import call_tetgen


def main(
    file,
    output_dir,
    alpha_fraction,
    min_faces,
    dfaces,
    simplify,
    Delta,
    tetgen_args=None,
    save_alpha_mesh=False,
    save_clean_swc=False,
):
    """Create watertight surface mesh from input Swc file.

    Takes as input the Swc file path and all assocciated hyperparameters of the algorithm.
    The Swc data, Mesh data and timings are returned.

    Args:
        file (string): path to Swc file
        output_dir (string): path to output directory
        alpha_fraction (float): positive number for alpha parameter
        min_faces (int): minimum number of faces for simplification stage
        dfaces (int): rate of increase for simplification stage.
        simplify (bool): flag to trigger simplification stage
        Delta (float): real parameter for Swc processing stage
        tetgen_args (string): optional tetgen parameters to call tetgen
        save_alpha_mesh (bool): flag to save the alpha-wrapped mesh
        save_clean_swc (bool): flag to save processed Swc

    Returns:
        swc (Swc): Swc containing cell data
        timings (dict): timings of stages of algorithm
        ms (pymeshlab.MeshSet) : simplified surface mesh
        mesh_name (string): path to mesh
        ms_alpha (pymeshlab.MeshSet) : alpha-wrapped mesh
    """
    # Begin recording time
    start = time.time()

    # Load and process the Swc file
    swc = Swc(file, True, Delta, Delta / 2)

    # store clean swc file
    if save_clean_swc:
        swc.write()

    # Create and save watertight surface mesh
    ms, mesh_name, ms_alpha = swc.make_mesh(
        simplify,
        output_dir=output_dir,
        min_faces=min_faces,
        dfaces=dfaces,
        alpha_fraction=alpha_fraction,
        save_alpha_mesh=save_alpha_mesh,
    )

    # Extract timings
    timings = swc.timings

    # Run Tetgen if desired
    if tetgen_args is not None:
        start_tet = time.time()
        call_tetgen(mesh_name, tetgen_args)
        timings["tetgen"] = time.time() - start_tet

    print(f"Completed {mesh_name}.")
    print(f"Total Elapsed time = {time.time()-start:.2f}")

    # Return data, for post-processing later
    return swc, timings, ms, mesh_name, ms_alpha


if __name__ == "__main__":
    description = """Reads swc file and produces a coarse watertight surface mesh. 
    Use the flag --help to see all available options."""

    # Read parameters and flags
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("file", help="Input SWC file.")
    parser.add_argument("--output_dir", help="Output directory for mesh")
    parser.add_argument(
        "--alpha",
        type=float,
        default=None,
        help="Alpha fraction for alpha wrapping step",
    )
    parser.add_argument(
        "--Delta",
        type=float,
        default=2.0,
        help="Smoothing parameter for skeleton of swc file.",
    )

    parser.add_argument("--simplify", type=int, help="Flag to simplify mesh", default=1)
    parser.add_argument(
        "--min_faces", type=int, help="Minimum faces for the mesh", default=None
    )
    parser.add_argument(
        "--dfaces",
        type=int,
        help="Rate to increase target number of faces in mesh",
        default=None,
    )
    parser.add_argument(
        "--tetgen_args", type=str, help="Parameters to pass into TetGen", default=None
    )
    parser.add_argument(
        "--save_alpha_mesh",
        type=int,
        help="Flag to save alpha wrapping mesh",
        default=0,
    )

    # Parse args
    args = parser.parse_args()

    # Extract boolean flags
    simplify = args.simplify == 1
    save_alpha_mesh = args.save_alpha_mesh == 1

    # Run function to create mesh
    swc, timings, ms, mesh_name, ms_alpha = main(
        args.file,
        args.output_dir,
        args.alpha,
        args.min_faces,
        args.dfaces,
        simplify,
        args.Delta,
        args.tetgen_args,
        save_alpha_mesh,
    )

    # Perform any further analysis needed here.
